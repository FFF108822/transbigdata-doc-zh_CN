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

import geopandas as gpd
import pandas as pd
from .grids import (
    GPS_to_grid,
    area_to_params,
    grid_to_centre,
    grid_to_polygon
)
from .coordinates import getdistance


def clean_same(data, col=['VehicleNum', 'Time', 'Lng', 'Lat']):
    '''
    删除信息与前后数据相同的数据以减少数据量  

    如：某个体连续n条数据除了时间以外其他信息都相同，则可以只保留首末两条数据

    Parameters
    -------
    data : DataFrame
        数据
    col : List
        列名，按[个体ID,时间,经度,纬度]的顺序，可以传入更多列。会以时间排序，再判断除了时间以外其他列的信息

    Returns
    -------
    data1 : DataFrame
        清洗后的数据
    '''
    [VehicleNum, Time, Lng, Lat] = col[:4]
    extra = col[4:]
    data1 = data.copy()
    data1 = data1.drop_duplicates(subset=[VehicleNum, Time])
    data1 = data1.sort_values(by=[VehicleNum, Time])
    data1['issame'] = 0
    for i in [VehicleNum, Lng, Lat]+extra:
        data1['issame'] += (data1[i].shift() == data1[i]
                            ) & (data1[i].shift(-1) == data1[i])
    data1 = data1[-(data1['issame'] == len([VehicleNum, Lng, Lat]+extra))]
    data1 = data1.drop('issame', axis=1)
    return data1

def clean_drift(data, col=['VehicleNum', 'Time', 'Lng', 'Lat'],
                speedlimit=80, dislimit=1000):
    '''
    删除漂移数据
    
    条件是，此数据与前后的速度都大于speedlimit，但前后数据之间的速度却小于speedlimit。
    传入的数据中时间列如果为datetime格式则计算效率更快

    Parameters
    -------
    data : DataFrame
        数据
    col : List
        列名，按[个体ID,时间,经度,纬度]的顺序    
    speedlimit : number
        速度限制(km/h)
    dislimit : number
        距离限制(m)

    Returns
    -------
    data1 : DataFrame
        清洗后的数据
    '''
    [VehicleNum, Time, Lng, Lat] = col
    data1 = data.copy()
    data1 = data1.drop_duplicates(subset=[VehicleNum, Time])
    data1[Time+'_dt'] = pd.to_datetime(data1[Time])
    data1 = data1.sort_values(by=[VehicleNum, Time])
    for i in [VehicleNum, Lng, Lat, Time+'_dt']:
        data1[i+'_pre'] = data1[i].shift()
        data1[i+'_next'] = data1[i].shift(-1)
    data1['dis_pre'] = getdistance(
        data1[Lng],
        data1[Lat],
        data1[Lng+'_pre'],
        data1[Lat+'_pre'])
    data1['dis_next'] = getdistance(
        data1[Lng],
        data1[Lat],
        data1[Lng+'_next'],
        data1[Lat+'_next'])
    data1['dis_prenext'] = getdistance(
        data1[Lng+'_pre'],
        data1[Lat+'_pre'],
        data1[Lng+'_next'],
        data1[Lat+'_next'])
    data1['timegap_pre'] = data1[Time+'_dt'] - data1[Time+'_dt_pre']
    data1['timegap_next'] = data1[Time+'_dt_next'] - data1[Time+'_dt']
    data1['timegap_prenext'] = data1[Time+'_dt_next'] - data1[Time+'_dt_pre']
    data1['speed_pre'] = data1['dis_pre'] / \
        data1['timegap_pre'].dt.total_seconds()*3.6
    data1['speed_next'] = data1['dis_next'] / \
        data1['timegap_next'].dt.total_seconds()*3.6
    data1['speed_prenext'] = data1['dis_prenext'] / \
        data1['timegap_prenext'].dt.total_seconds()*3.6
    if speedlimit:
        data1 = data1[
            -((data1[VehicleNum+'_pre'] == data1[VehicleNum]) &
              (data1[VehicleNum+'_next'] == data1[VehicleNum]) &
                (data1['speed_pre'] > speedlimit) &
              (data1['speed_next'] > speedlimit) &
              (data1['speed_prenext'] < speedlimit))]
    if dislimit:
        data1 = data1[
            -((data1[VehicleNum+'_pre'] == data1[VehicleNum]) &
              (data1[VehicleNum+'_next'] == data1[VehicleNum]) &
              (data1['dis_pre'] > dislimit) &
              (data1['dis_next'] > dislimit) &
              (data1['dis_prenext'] < dislimit))]
    data1 = data1[data.columns]
    return data1


def clean_outofbounds(data, bounds, col=['Lng', 'Lat']):
    '''
    剔除超出研究范围的数据

    Parameters
    -------
    data : DataFrame
        数据
    bounds : List    
        研究范围的左下右上经纬度坐标，顺序为[lon1,lat1,lon2,lat2]
    col : List
        经纬度列名

    Returns
    -------
    data1 : DataFrame
        研究范围内的数据
    '''
    lon1, lat1, lon2, lat2 = bounds
    if (lon1 > lon2) | (lat1 > lat2) | (abs(lat1) > 90) | (
            abs(lon1) > 180) | (abs(lat2) > 90) | (abs(lon2) > 180):
        raise Exception(
            'Bounds error. The input bounds should be in the order \
of [lon1,lat1,lon2,lat2]. (lon1,lat1) is the lower left corner and \
(lon2,lat2) is the upper right corner.')
    Lng, Lat = col
    data1 = data.copy()
    data1 = data1[(data1[Lng] > bounds[0]) & (data1[Lng] < bounds[2]) & (
        data1[Lat] > bounds[1]) & (data1[Lat] < bounds[3])]
    return data1


def clean_outofshape(data, shape, col=['Lng', 'Lat'], accuracy=500):
    '''
    剔除超出研究区域的数据

    输入研究范围的GeoDataFrame，剔除超出研究区域的数据，计算原理是先栅格化后剔除

    Parameters
    -------
    data : DataFrame
        数据
    shape : GeoDataFrame    
        研究范围的GeoDataFrame
    col : List
        经纬度列名
    accuracy : number
        定义栅格大小，越小精度越高

    Returns
    -------
    data1 : DataFrame
        研究范围内的数据
    '''
    Lng, Lat = col
    shape_unary = shape.unary_union
    bounds = shape_unary.bounds
    params = area_to_params(bounds, accuracy)
    data1 = data.copy()
    data1['LONCOL'], data1['LATCOL'] = GPS_to_grid(
        data1[Lng], data1[Lat], params)
    data1_gdf = data1[['LONCOL', 'LATCOL']].drop_duplicates()
    data1_gdf['geometry'] = grid_to_polygon(
        [data1_gdf['LONCOL'], data1_gdf['LATCOL']], params)
    data1_gdf = gpd.GeoDataFrame(data1_gdf)
    data1_gdf = data1_gdf[data1_gdf.intersects(shape_unary)]
    data1 = pd.merge(data1, data1_gdf[['LONCOL', 'LATCOL']]).drop(
        ['LONCOL', 'LATCOL'], axis=1)
    return data1


def clean_traj(data, col=['uid', 'str_time', 'lon', 'lat'], tripgap=1800,
               disgap=50000, speedlimit=80):
    '''
    轨迹数据清洗组合拳（实验中）
    
    包括定义时间长度阈值以及距离阈值，超出阈值视为新的轨迹

    Parameters
    -------
    data : DataFrame
        轨迹数据
    col : List
        列名，以[个体id,时间,经度,纬度]排列
    tripgap : number
        多长时间（秒）视为新的出行
    disgap : number
        多长距离（米）视为新的出行
    speedlimit : number
        车速限制

    Returns
    -------
    data1 : DataFrame
        清洗后的数据
    '''
    uid, timecol, lon, lat = col
    data[timecol] = pd.to_datetime(data[timecol])
    data = data.sort_values(by=[uid, timecol])
    cols = []
    for i in data.columns:
        if i not in [uid, timecol, lon, lat]:
            cols.append(i)
    data = clean_same(data, col=[uid, timecol, lon, lat]+cols)
    data = clean_drift(data, col=[uid, timecol, lon, lat],
                       speedlimit=speedlimit)
    data = id_reindex(data, uid, timecol=timecol, timegap=tripgap)
    data = data.rename(columns={uid+'_new': 'tripid'})
    data = id_reindex_disgap(
        data, col=['tripid', lon, lat], disgap=disgap, suffix='')
    data1 = data.copy()
    data1['lon1'] = data1[lon].shift(-1)
    data1['lat1'] = data1[lat].shift(-1)
    data1['tripid1'] = data1['tripid'].shift(-1)
    data1 = data1[data1['tripid'] == data1['tripid1']]
    data1['dis'] = getdistance(
        data1[lon], data1[lat], data1['lon1'], data1['lat1'])
    a = data1.groupby(['tripid'])['dis'].sum()
    a = a[-(a < 50)].reset_index()['tripid']
    data = pd.merge(data, a)
    data = data.drop('tripid', axis=1)
    data = id_reindex(data, uid, timecol=timecol, timegap=tripgap)
    data = data.rename(columns={uid+'_new': 'tripid'})
    data = id_reindex_disgap(
        data, col=['tripid', lon, lat], disgap=disgap, suffix='')
    return data

def dataagg(data, shape, col=['Lng', 'Lat', 'count'], accuracy=500):
    '''
    数据集计至小区

    Parameters
    -------
    data : DataFrame
        数据
    shape : GeoDataFrame
        小区
    col : List
        可传入经纬度两列，如['Lng','Lat']，此时每一列权重为1。也可以传入经纬度和计数列三列，如['Lng','Lat','count']
    accuracy : number
        计算原理是先栅格化后集计，这里定义栅格大小，越小精度越高

    Returns
    -------
    aggresult : GeoDataFrame
        小区，其中count列为统计结果
    data1 : DataFrame
        数据，对应上了小区
    '''
    if len(col) == 2:
        Lng, Lat = col
        aggcol = None
    else:
        Lng, Lat, aggcol = col
    shape['index'] = range(len(shape))
    shape_unary = shape.unary_union
    bounds = shape_unary.bounds
    params = area_to_params(bounds, accuracy)
    data1 = data.copy()
    data1['LONCOL'], data1['LATCOL'] = GPS_to_grid(
        data1[Lng], data1[Lat], params)
    data1_gdf = data1[['LONCOL', 'LATCOL']].drop_duplicates()
    data1_gdf['geometry'] = gpd.points_from_xy(
        *grid_to_centre([data1_gdf['LONCOL'], data1_gdf['LATCOL']], params))
    data1_gdf = gpd.GeoDataFrame(data1_gdf)
    data1_gdf = gpd.sjoin(data1_gdf, shape, how='left')
    data1 = pd.merge(data1, data1_gdf).drop(['LONCOL', 'LATCOL'], axis=1)
    if aggcol:
        aggresult = pd.merge(shape, data1.groupby('index')[
                             aggcol].sum().reset_index()).drop('index', axis=1)
    else:
        data1['_'] = 1
        aggresult = pd.merge(shape, data1.groupby('index')['_'].sum().rename(
            'count').reset_index()).drop('index', axis=1)
        data1 = data1.drop('_', axis=1)
    data1 = data1.drop('index', axis=1)
    return aggresult, data1


def id_reindex_disgap(data, col=['uid', 'lon', 'lat'], disgap=1000,
                      suffix='_new'):
    '''
    对数据的ID列重新编号
    
    如果相邻两条记录超过距离，则编号为新id

    Parameters
    -------
    data : DataFrame
        数据 
    col : str
        要重新编号的ID列名
    disgap : number
        如果个体轨迹超过一定距离，则编号为新的个体。
    suffix : str
        新编号列名的后缀

    Returns
    -------
    data1 : DataFrame
        重新编号的数据
    '''
    uid, lon, lat = col
    data1 = data.copy()
    data1[uid+suffix] = (
        (data1[uid].shift() != data1[uid]) |
        (getdistance(data1[lon],
                     data1[lat],
                     data1[lon].shift(),
                     data1[lat].shift()) > disgap)).astype(int).cumsum()-1
    a = data1.groupby([uid+suffix])[lon].count()
    data1 = pd.merge(data1, a[a > 1].reset_index()[[uid+suffix]])
    return data1


def id_reindex(data, col, new=False, timegap=None, timecol=None,
               suffix='_new', sample=None):
    '''
    对数据的ID列重新编号

    Parameters
    -------
    data : DataFrame
        数据 
    col : str
        要重新编号的ID列名
    new : bool
        False，相同ID的新编号相同；True，依据表中的顺序，ID再次出现则编号不同
    timegap : number
        如果个体在一段时间内没出现（timegap为时间阈值），则编号为新的个体。此参数与timecol同时设定才有效果。
    timecol : str
        时间字段名称，此参数与timegap同时设定才有效果。
    suffix : str
        新编号列名的后缀，设置为False时替代原有列名
    sample : int
        传入数值，对重新编号的个体进行抽样

    Returns
    -------
    data1 : DataFrame
        重新编号的数据
    '''
    if not suffix:
        suffix = ''
    data1 = data.copy()
    if new:
        data1[col+suffix] = data1[col] != data1[col].shift()
        data1[col+suffix] = data1[col+suffix].cumsum()-1
    else:
        tmp = data1[[col]].drop_duplicates()
        tmp[col+'_'] = range(len(tmp))
        data1 = pd.merge(data1, tmp, on=col)
        data1[col+suffix] = data1[col+'_']
        if suffix != '_':
            data1 = data1.drop(col+'_', axis=1)
    if (timegap is not None) & (timecol is not None):
        data1[timecol] = pd.to_datetime(data1[timecol])
        data1 = data1.sort_values(by=[col+suffix, timecol])
        data1[col+suffix] = (
            (data1[col+suffix].shift() != data1[col+suffix]) |
            ((data1[timecol]-data1[timecol].shift()).dt.total_seconds()
             > timegap)).astype(int).cumsum()-1

    if sample:
        tmp = data1[col+suffix].drop_duplicates().sample(sample)
        data1 = pd.merge(data1, tmp)
    return data1
