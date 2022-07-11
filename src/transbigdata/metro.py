'''
BSD 3-Clause License

Copyright (c) 2021, Qing Yu
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import pandas as pd
import numpy as np
from shapely.geometry import LineString


def split_subwayline(line, stop):
    '''
    切分线路得到断面，可用于可视化

    用公交/地铁站点对公交/地铁线进行切分，得到断面，可用于可视化

    Parameters
    -------
    line : GeoDataFrame
        公交/地铁线路
    stop : GeoDataFrame
        公交/地铁站点

    Returns
    -------
    metro_line_splited : GeoDataFrame
        生成的断面线型
    '''
    def getline(r2, line_geometry):
        ls = []
        if r2['o_project'] <= r2['d_project']:
            tmp1 = np.linspace(r2['o_project'], r2['d_project'], 10)
        if r2['o_project'] > r2['d_project']:
            tmp1 = np.linspace(
                r2['o_project']-line_geometry.length, r2['d_project'], 10)
            tmp1[tmp1 < 0] = tmp1[tmp1 < 0]+line_geometry.length
        for j in tmp1:
            ls.append(line_geometry.interpolate(j))
        return LineString(ls)
    lss = []
    for k in range(len(line)):
        r = line.iloc[k]
        line_geometry = r['geometry']
        tmp = stop[stop['linename'] == r['linename']].copy()
        for i in tmp.columns:
            tmp[i+'1'] = tmp[i].shift(-1)
        tmp = tmp.iloc[:-1]
        tmp = tmp[['stationnames', 'stationnames1',
                   'geometry', 'geometry1', 'linename', 'line']]
        tmp['o_project'] = tmp['geometry'].apply(
            r['geometry'].project)
        tmp['d_project'] = tmp['geometry1'].apply(
            r['geometry'].project)
        tmp['geometry'] = tmp.apply(
            lambda r2: getline(r2, line_geometry), axis=1)
        lss.append(tmp)
    metro_line_splited = pd.concat(lss).drop('geometry1', axis=1)
    metro_line_splited.crs = 'epsg:4326'
    metro_line_splited['length'] = metro_line_splited.to_crs(epsg=3857).length
    metro_line_splited = metro_line_splited.drop(
        ['o_project', 'd_project'], axis=1)
    return metro_line_splited


def metro_network(line, stop, transfertime=5, nxgraph=True):
    '''
    构建地铁网络

    输入站点信息，输出网络信息，可用于最短路径与最短k路径生成。该方法依赖于NetworkX。
    地铁出行时间由以下部分构成：地铁运行时间（距离/速度）+停站时间（一般取固定值）+换乘时间（步行时间+等车时间）

    Parameters
    -------
    line : GeoDataFrame
        地铁线路，`line`列存储地铁线路名称，`speed`存储每条地铁线路运行车速，`stoptime`每条线路停站时间
    stop : GeoDataFrame
        公交站点
    transfertime : number
        每个轨道换乘的时长
    nxgraph : bool
        默认True，如果True则直接输出由NetworkX构建的网络G，如果为False，则输出网络的边edge1,edge2和
        节点node，以便用于精确定义边权

    Returns
    -------
    G : networkx.classes.graph.Graph
        nxgraph为True时输出: networkx构建的网络G
    edge1 : DataFrame
        nxgraph为False时输出: 轨道断面的边
    edge2 : DataFrame
        nxgraph为False时输出: 轨道换乘的边
    node : List
        nxgraph为False时输出: 网络节点
    '''
    # Obtain edge1: Network edge for line section.
    linestop = stop.copy()
    if ('speed' not in line.columns) | ('stoptime' not in line.columns):
        raise ValueError(
            'Lines should have `line` column to store line name,'
            '`speed` column to store metro speed and'
            '`stoptime` column to store stop time at each station'
        )
    for i in linestop.columns:
        linestop[i+'1'] = linestop[i].shift(-1)
    linestop = linestop[linestop['linename'] == linestop['linename1']].copy()
    linestop = linestop.rename(
        columns={'stationnames': 'ostop', 'stationnames1': 'dstop'})
    linestop['ostation'] = linestop['line']+linestop['ostop']
    linestop['dstation'] = linestop['line']+linestop['dstop']
    edge1 = linestop[['ostation', 'dstation']].copy()

    # calculate travel time for edge1
    # calculate distance
    metrolinesplit = split_subwayline(line, stop)
    metrolinesplit['ostation'] = metrolinesplit['line'] + \
        metrolinesplit['stationnames']
    metrolinesplit['dstation'] = metrolinesplit['line'] + \
        metrolinesplit['stationnames1']
    metrolinesplit = metrolinesplit[['ostation', 'dstation', 'line', 'length']]
    edge1 = pd.merge(edge1, metrolinesplit, how='left')
    edge1 = pd.merge(edge1, line[['line', 'speed', 'stoptime']])

    # calculate duration
    edge1['duration'] = 60*(edge1['length']/1000) / \
        edge1['speed']+edge1['stoptime']
    edge1 = edge1[['ostation', 'dstation', 'duration']].drop_duplicates(
        subset=['ostation', 'dstation'])

    # Obtain edge2: Network edge for transfering.
    linestop = stop.copy()
    linestop['station'] = linestop['line'] + linestop['stationnames']
    tmp = linestop.groupby(['stationnames'])[
        'linename'].count().rename('count').reset_index()
    tmp = pd.merge(linestop, tmp[tmp['count'] > 2]
                   ['stationnames'], on='stationnames')
    tmp = tmp[['stationnames', 'line', 'station']].drop_duplicates()
    tmp = pd.merge(tmp, tmp, on='stationnames')

    edge2 = tmp[tmp['line_x'] != tmp['line_y']][['station_x', 'station_y']]
    # All transfer time are set as the same, export `edge2` for further degign
    edge2['duration'] = transfertime
    edge2.columns = edge1.columns
    edge = edge1.append(edge2)
    node = list(edge['ostation'].drop_duplicates())
    if nxgraph:
        import networkx as nx
        G = nx.Graph()
        G.add_nodes_from(node)
        G.add_weighted_edges_from(edge.values)
        return G
    else:
        return edge1, edge2, node


def get_shortest_path(G, stop, ostation, dstation):
    '''
    获取最短路径

    Parameters
    -------
    G : networkx.classes.graph.Graph
        networkx构建的地铁网络G
    stop : DataFrame
        地铁站点信息表
    ostation : str
        O站点名称
    dstation : str
        D站点名称

    Returns
    -------
    path : list
        路径，一个包含路径经过节点名称的list
    '''
    import networkx as nx
    o = stop[stop['stationnames'] == ostation]['line'].iloc[0]+ostation
    d = stop[stop['stationnames'] == dstation]['line'].iloc[0]+dstation
    return nx.shortest_path(G, source=o, target=d, weight='weight')


def get_k_shortest_paths(G, stop, ostation, dstation, k):
    '''
    获取前k个最短路径

    Parameters
    -------
    G : networkx.classes.graph.Graph
        networkx构建的地铁网络G
    stop : DataFrame
        地铁站点信息表
    ostation : str
        O站点名称
    dstation : str
        D站点名称
    k : int
        获取前k个路径

    Returns
    -------
    paths : list
        包含前k个路径的list
    '''
    from itertools import islice
    import networkx as nx
    o = stop[stop['stationnames'] == ostation]['line'].iloc[0]+ostation
    d = stop[stop['stationnames'] == dstation]['line'].iloc[0]+dstation
    return list(
        islice(nx.shortest_simple_paths(G, o, d, weight='weight'), k)
    )


def get_path_traveltime(G, path):
    '''
    通过路径获得出行时间

    Parameters
    -------
    G : networkx.classes.graph.Graph
        networkx构建的地铁网络G
    path : list
        路径，一个包含路径经过节点名称的list

    Returns
    -------
    traveltime : float
        该路径的出行时间
    '''
    traveltime = 0
    for i in range(len(path)-1):
        traveltime += G.get_edge_data(path[i], path[i+1])['weight']
    return traveltime
