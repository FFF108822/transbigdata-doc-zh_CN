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
from .grids import GPS_to_grid, grid_to_centre


def odagg_grid(oddata, params, col=['slon', 'slat', 'elon', 'elat'],
               arrow=False, **kwargs):
    '''
    OD集计与地理信息生成（栅格）。输入OD数据（每一行数据是一个出行），栅格化OD并集计后生成OD的GeoDataFrame


    Parameters
    -------
    oddata : DataFrame 
        OD数据
    col : List
        起终点列名,['slon','slat','elon','elat']，此时每一列权重为1。
        也可以传入权重列，如['slon','slat','elon','elat','count']
    params : List
        栅格参数(lonStart,latStart,deltaLon,deltaLat)，分别为栅格左下角坐标与单个栅格的经纬度长宽
    arrow : bool
        生成的OD地理线型是否包含箭头

    Returns
    -------
    oddata1 : GeoDataFrame 
        集计后生成OD的GeoDataFrame
    '''
    if len(col) == 4:
        [slon, slat, elon, elat] = col
        count = 'count'
    if len(col) == 5:
        [slon, slat, elon, elat, count] = col
    oddata['SLONCOL'], oddata['SLATCOL'] = GPS_to_grid(
        oddata[slon], oddata[slat], params)
    oddata['ELONCOL'], oddata['ELATCOL'] = GPS_to_grid(
        oddata[elon], oddata[elat], params)
    if len(col) == 4:
        oddata[count] = 1
    oddata_agg = oddata.groupby(['SLONCOL', 'SLATCOL', 'ELONCOL', 'ELATCOL'])[
        count].sum().reset_index()
    oddata_agg['SHBLON'], oddata_agg['SHBLAT'] = grid_to_centre(
        [oddata_agg['SLONCOL'], oddata_agg['SLATCOL']], params)
    oddata_agg['EHBLON'], oddata_agg['EHBLAT'] = grid_to_centre(
        [oddata_agg['ELONCOL'], oddata_agg['ELATCOL']], params)
    from shapely.geometry import LineString
    if arrow:
        oddata_agg['geometry'] = oddata_agg.apply(lambda r: tolinewitharrow(
            r['SHBLON'], r['SHBLAT'], r['EHBLON'], r['EHBLAT'],
            **kwargs), axis=1)
    else:
        oddata_agg['geometry'] = oddata_agg.apply(lambda r: LineString(
            [[r['SHBLON'], r['SHBLAT']], [r['EHBLON'], r['EHBLAT']]]), axis=1)
    oddata_agg = gpd.GeoDataFrame(oddata_agg)
    oddata_agg = oddata_agg.sort_values(by=count)
    return oddata_agg


def odagg_shape(oddata, shape, col=['slon', 'slat', 'elon', 'elat'],
                params=None, round_accuracy=6, arrow=False, **kwargs):
    '''
    OD集计与地理信息生成（小区集计）。输入OD数据（每一行数据是一个出行），栅格化OD并集计后生成OD的GeoDataFrame

    Parameters
    -------
    oddata : DataFrame 
        OD数据
    shape : GeoDataFrame
        集计小区的GeoDataFrame
    col : List   
        起终点列名,['slon','slat','elon','elat']，此时每一列权重为1。
        也可以传入权重列，如['slon','slat','elon','elat','count']
    params : List 
        栅格化参数，如果传入，则先栅格化后以栅格中心点匹配小区，如果不传入，则直接以经纬度匹配。在数据量大时，用栅格化进行匹配速度会极大提升
    round_accuracy : number
        集计时经纬度取小数位数
    arrow : bool       
        生成的OD地理线型是否包含箭头
    
    Returns
    -------
    oddata1 : GeoDataFrame
        集计后生成OD的GeoDataFrame
    '''
    if len(col) == 4:
        [slon, slat, elon, elat] = col
        count = 'count'
    if len(col) == 5:
        [slon, slat, elon, elat, count] = col
    shape_1 = shape.copy()
    shape['x'] = shape.centroid.x
    shape['y'] = shape.centroid.y
    shape = shape[['x', 'y', 'geometry']]
    if params:
        oddata['SLONCOL'], oddata['SLATCOL'] = GPS_to_grid(
            oddata[slon], oddata[slat], params)
        oddata['ELONCOL'], oddata['ELATCOL'] = GPS_to_grid(
            oddata[elon], oddata[elat], params)
        if len(col) == 4:
            oddata[count] = 1
        oddata_agg = oddata.groupby([
            'SLONCOL', 'SLATCOL', 'ELONCOL', 'ELATCOL'])[
                count].sum().reset_index()
        oddata_agg['SHBLON'], oddata_agg['SHBLAT'] = grid_to_centre(
            [oddata_agg['SLONCOL'], oddata_agg['SLATCOL']], params)
        oddata_agg['EHBLON'], oddata_agg['EHBLAT'] = grid_to_centre(
            [oddata_agg['ELONCOL'], oddata_agg['ELATCOL']], params)
        a = oddata_agg[['SHBLON', 'SHBLAT']]
        b = oddata_agg[['EHBLON', 'EHBLAT']]
        a.columns = ['lon', 'lat']
        b.columns = ['lon', 'lat']
        c = pd.concat([a, b]).drop_duplicates()
        d = c[['lon', 'lat']].drop_duplicates()
        d['geometry'] = gpd.points_from_xy(d['lon'], d['lat'])
        d = gpd.GeoDataFrame(d)
        d = gpd.sjoin(d, shape)
        c = pd.merge(c, d)
        c = c[['lon', 'lat', 'index_right', 'x', 'y']]
        c.columns = ['SHBLON', 'SHBLAT', 'sindex', 'sx', 'sy']
        oddata_agg = pd.merge(oddata_agg, c)
        c.columns = ['EHBLON', 'EHBLAT', 'eindex', 'ex', 'ey']
        oddata_agg = pd.merge(oddata_agg, c)
        oddata_agg = oddata_agg.groupby([
            'sindex', 'sx', 'sy', 'eindex', 'ex', 'ey'])[
            count].sum().reset_index()
    else:
        a = oddata[[slon, slat]]
        b = oddata[[elon, elat]]
        a.columns = ['lon', 'lat']
        b.columns = ['lon', 'lat']
        c = pd.concat([a, b]).drop_duplicates()
        c['lon_simple'] = c['lon'].round(round_accuracy)
        c['lat_simple'] = c['lat'].round(round_accuracy)
        d = c[['lon_simple', 'lat_simple']].drop_duplicates()
        d['geometry'] = gpd.points_from_xy(d['lon_simple'], d['lat_simple'])
        d = gpd.GeoDataFrame(d)
        d = gpd.sjoin(d, shape)
        c = pd.merge(c, d)
        c = c[['lon', 'lat', 'index_right', 'x', 'y']]
        c.columns = ['slon', 'slat', 'sindex', 'sx', 'sy']
        oddata = pd.merge(oddata, c)
        c.columns = ['elon', 'elat', 'eindex', 'ex', 'ey']
        oddata = pd.merge(oddata, c)
        if len(col) == 4:
            oddata[count] = 1
        oddata_agg = oddata.groupby([
            'sindex', 'sx', 'sy', 'eindex', 'ex', 'ey'])[
            count].sum().reset_index()
    from shapely.geometry import LineString
    if arrow:
        oddata_agg['geometry'] = oddata_agg.apply(lambda r: tolinewitharrow(
            r['sx'], r['sy'], r['ex'], r['ey'], **kwargs), axis=1)
    else:
        oddata_agg['geometry'] = oddata_agg.apply(lambda r: LineString(
            [[r['sx'], r['sy']], [r['ex'], r['ey']]]), axis=1)
    oddata_agg = gpd.GeoDataFrame(oddata_agg)
    oddata_agg = oddata_agg[['sindex', 'eindex', count, 'geometry']]
    oddata_agg = pd.merge(oddata_agg, shape_1.reset_index().rename(
        columns={'index': 'sindex'}).drop('geometry', axis=1), on='sindex')
    oddata_agg = pd.merge(oddata_agg, shape_1.reset_index().rename(
        columns={'index': 'eindex'}).drop('geometry', axis=1), on='eindex')
    oddata_agg = oddata_agg.sort_values(by=count)
    return oddata_agg


def tolinewitharrow(x1, y1, x2, y2, theta=20, length=0.1, pos=0.8):
    '''
    Input start and end coords，Returns LineString with arrow

    Parameters
    -------
    x1,y1,x2,y2 : float
        xy coords of start and end coords
    theta : float
        Angle of arrow
    length : float
        The length ratio of the arrow to the original line. For example, if the
        length of the original line is 1 and the length is set to 0.3, the
        arrow size is 0.3
    pos : float
        Position of arrow, 0 at the start point, 1 at the end point

    Returns
    -------
    Line : MultiLineString
        OD LineString with arrow
    '''
    import numpy as np
    from shapely.geometry import MultiLineString
    l_main = [[x1, y1], [x2, y2]]
    p1, p2 = (1-pos)*x1+pos*x2, (1-pos)*y1+pos*y2
    R = np.array([[np.cos(np.radians(theta)), -np.sin(np.radians(theta))],
                  [np.sin(np.radians(theta)), np.cos(np.radians(theta))]])
    l1 = np.dot(R, np.array([[x1-x2, y1-y2]]).T).T[0] * \
        length+np.array([p1, p2]).T
    l1 = [list(l1), [p1, p2]]
    R = np.array([[np.cos(np.radians(-theta)), -np.sin(np.radians(-theta))],
                  [np.sin(np.radians(-theta)), np.cos(np.radians(-theta))]])
    l2 = np.dot(R, np.array([[x1-x2, y1-y2]]).T).T[0] * \
        length+np.array([p1, p2]).T
    l2 = [list(l2), [p1, p2]]
    return MultiLineString([l_main, l1, l2])
