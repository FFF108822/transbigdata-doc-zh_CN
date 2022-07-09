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

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import itertools
from operator import itemgetter
import geopandas as gpd
import math
from .coordinates import getdistance


def ckdnearest(dfA_origin,
               dfB_origin,
               Aname=['lon', 'lat'],
               Bname=['lon', 'lat']):
    '''
    输入两个DataFrame，分别指定经纬度列名，为表A匹配表B中最近点，并计算距离

    Parameters
    -------
    dfA_origin : DataFrame
        表A
    dfB_origin : DataFrame
        表B
    Aname : List
        表A中经纬度列字段
    Bname : List
        表B中经纬度列字段

    Returns
    -------
    gdf : DataFrame
        为A匹配到B上最近点的表
    '''
    if len(dfA_origin) == 0:
        raise Exception('The input DataFrame dfA is empty')
    if len(dfB_origin) == 0:
        raise Exception('The input DataFrame dfB is empty')
    gdA = dfA_origin.copy()
    gdB = dfB_origin.copy()
    from scipy.spatial import cKDTree
    btree = cKDTree(gdB[Bname].values)
    dist, idx = btree.query(gdA[Aname].values, k=1)
    gdA['index'] = idx
    gdB['index'] = range(len(gdB))
    gdf = pd.merge(gdA, gdB, on='index')
    if (Aname[0] == Bname[0]) & (Aname[1] == Bname[1]):
        gdf['dist'] = getdistance(
            gdf[Aname[0]+'_x'],
            gdf[Aname[1]+'_y'],
            gdf[Bname[0]+'_x'],
            gdf[Bname[1]+'_y'])
    else:
        gdf['dist'] = getdistance(
            gdf[Aname[0]],
            gdf[Aname[1]],
            gdf[Bname[0]],
            gdf[Bname[1]])
    return gdf


def ckdnearest_point(gdA, gdB):
    '''
    输入两个GeoDataFrame，gdfA、gdfB均为点，该方法会为gdfA表连接上gdfB中最近的点，并添加距离字段dist

    Parameters
    -------
    gdA : GeoDataFrame
        表A，点要素
    gdB : GeoDataFrame
        表B，点要素

    Returns
    -------
    gdf : GeoDataFrame
        为A匹配到B上最近点的表
    '''
    if len(gdA) == 0:
        raise Exception('The input GeoDataFrame gdfA is empty')
    if len(gdB) == 0:
        raise Exception('The input GeoDataFrame gdfB is empty')
    nA = np.array(list(gdA.geometry.apply(lambda x: (x.x, x.y))))
    nB = np.array(list(gdB.geometry.apply(lambda x: (x.x, x.y))))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdA['dist'] = dist
    gdA['index'] = idx
    gdB['index'] = range(len(gdB))
    gdf = pd.merge(gdA, gdB, on='index')
    return gdf

def ckdnearest_line(gdfA, gdfB):
    '''
    输入两个GeoDataFrame，其中gdfA为点，gdfB为线，该方法会为gdfA表连接上gdfB中最近的线，并添加距离字段dist

    Parameters
    -------
    gdA : GeoDataFrame
        表A，点要素
    gdB : GeoDataFrame
        表B，线要素

    Returns
    -------
    gdf : GeoDataFrame
        为A匹配到B中最近的线
    '''
    if len(gdfA) == 0:
        raise Exception('The input GeoDataFrame gdfA is empty')
    if len(gdfB) == 0:
        raise Exception('The input GeoDataFrame gdfB is empty')
    A = np.concatenate(
        [np.array(geom.coords) for geom in gdfA.geometry.to_list()])
    B = [np.array(geom.coords) for geom in gdfB.geometry.to_list()]
    B_ix = tuple(itertools.chain.from_iterable(
        [itertools.repeat(i, x) for i, x in enumerate(list(map(len, B)))]))
    B = np.concatenate(B)
    ckd_tree = cKDTree(B)
    dist, idx = ckd_tree.query(A, k=1)
    idx = itemgetter(*idx)(B_ix)
    gdfA['dist'] = dist
    gdfA['index'] = idx
    gdfB['index'] = range(len(gdfB))
    gdf = pd.merge(gdfA, gdfB, on='index')
    return gdf

def splitline_with_length(Centerline, maxlength=100):
    '''
    输入线GeoDataFrame要素，打断为最大长度maxlength的小线段

    Parameters
    -------
    Centerline : GeoDataFrame
        线要素
    maxlength : number
        打断的线段最大长度

    Returns
    -------
    splitedline : GeoDataFrame
        打断后的线
    '''
    def splitline(route, maxlength):
        routelength = route.length
        from shapely.geometry import LineString
        lss = []
        for k in range(int(routelength/maxlength)+1):
            if k == int(routelength/maxlength):
                lm = routelength
            else:
                lm = (k+1)*maxlength
            a = np.linspace(k*maxlength, lm, 10)
            ls = []
            for line in a:
                ls.append(route.interpolate(line))
            lss.append(LineString(ls))
        lss = gpd.GeoDataFrame(lss, columns=['geometry'])
        return lss
    lsss = []
    for i in range(len(Centerline)):
        route = Centerline['geometry'].iloc[i]
        lss = splitline(route, maxlength)
        lss['id'] = i
        lsss.append(lss)
    lsss = pd.concat(lsss)
    lsss['length'] = lsss.length
    splitedline = lsss
    return splitedline


def merge_polygon(data, col):
    '''
    输入多边形GeoDataFrame数据，以及分组列名col，对不同组别进行分组的多边形进行合并


    Parameters
    -------
    data : GeoDataFrame
        多边形数据
    col : str
        分组列名

    Returns
    -------
    data1 : GeoDataFrame
        合并后的面
    '''
    groupnames = []
    geometries = []
    for i in data[col].drop_duplicates():
        groupnames.append(i)
        geometries.append(data[data[col] == i].unary_union)
    data1 = gpd.GeoDataFrame()
    data1['geometry'] = geometries
    data1[col] = groupnames
    return data1


def polyon_exterior(data, minarea=0):
    '''
    输入多边形GeoDataFrame数据，对多边形取外边界构成新多边形

    Parameters
    -------
    data : GeoDataFrame
        多边形数据
    minarea : number
        最小面积，小于这个面积的面全部剔除

    Returns
    -------
    data1 : GeoDataFrame
        处理后的面
    '''
    data1 = data.copy()

    def polyexterior(p):
        from shapely.geometry import Polygon, MultiPolygon
        if type(p) == MultiPolygon:
            geometries = []
            for i in p:
                poly = Polygon(i.exterior)
                if minarea > 0:
                    if poly.area > minarea:
                        geometries.append(poly)
                else:
                    geometries.append(poly)
            return MultiPolygon(geometries)
        if type(p) == Polygon:
            return Polygon(p.exterior)
    data1['geometry'] = data1['geometry'].apply(polyexterior)
    data1 = data1[-data1['geometry'].is_empty]
    return data1


def ellipse_params(data, col=['lon', 'lat'], confidence=95, epsg=None):
    '''
    置信椭圆参数估计：输入点数据，获取置信椭圆的参数

    Parameters
    -------
    data : DataFrame
        点数据
    confidence : number
        置信度，可选99，95，90
    epsg : number
        如果给了，则将原始坐标从wgs84，转换至给定epsg坐标系下进行置信椭圆参数估计
    col: List
        以[经度，纬度]形式存储的列名

    Returns
    -------
    params: List
        质心椭圆参数，分别为[pos,width,height,theta,area,alpha]
        对应[中心点坐标，短轴，长轴，角度，面积，方向性]
    '''
    lon, lat = col
    if confidence == 99:
        nstd = 9.210**0.5
    if confidence == 95:
        nstd = 5.991**0.5
    if confidence == 90:
        nstd = 4.605**0.5
    points = data.copy()
    points = gpd.GeoDataFrame(points)
    points['geometry'] = gpd.points_from_xy(points[lon], points[lat])
    if epsg:
        points.crs = {'init': 'epsg:4326'}
        points = points.to_crs(epsg=epsg)
    point_np = np.array([points.geometry.x, points.geometry.y]).T
    pos = point_np.mean(axis=0)
    cov = np.cov(point_np, rowvar=False)
    vals, vecs = np.linalg.eigh(cov)
    theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    width, height = 2 * nstd * np.sqrt(vals)
    area = width/2*height/2*math.pi
    oblateness = (height-width)/height

    ellip_params = [pos, width, height, theta, area, oblateness]
    return ellip_params


def ellipse_plot(ellip_params, ax, **kwargs):
    '''
    置信椭圆绘制：输入置信椭圆的参数，绘制置信椭圆

    Parameters
    -------
    ellip_params : List
        质心椭圆参数，分别为[pos,width,height,theta,area,alpha]
        对应[中心点坐标，短轴，长轴，角度，面积，方向性]
    ax : matplotlib.axes._subplots.AxesSubplot
        绘图的matplotlib.axes
    '''
    [pos, width, height, theta, area, alpha] = ellip_params
    from matplotlib.patches import Ellipse
    ellip = Ellipse(xy=pos, width=width, height=height,
                    angle=theta, linestyle='-', **kwargs)
    ax.add_artist(ellip)
