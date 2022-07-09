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
import numpy as np
from .preprocess import id_reindex


def traj_densify(data, col=['Vehicleid', 'Time', 'Lng', 'Lat'], timegap=15):
    '''
    轨迹点增密，确保每隔timegap秒会有一个轨迹点

    Parameters
    -------
    data : DataFrame
        数据
    col : List
        列名，按[车辆ID,时间,经度,纬度]的顺序
    timegap : number
        单位为秒，每隔多长时间插入一个轨迹点

    Returns
    -------
    data1 : DataFrame
        处理后的数据
    '''
    pass


def traj_sparsify(data, col=['Vehicleid', 'Time', 'Lng', 'Lat'], timegap=15,
                  method='subsample'):
    '''
    轨迹点稀疏化。轨迹数据采样间隔过高的时候，数据量太大，不便于分析。这个函数可以将采样间隔扩大，缩减数据量

    Parameters
    -------
    data : DataFrame
        数据
    col : List
        列名，按[车辆ID,时间,经度,纬度]的顺序
    timegap : number
        单位为秒，每隔多长时间一个轨迹点
    method : str
        可选`interpolate`插值或`subsample`子采样

    Returns
    -------
    data1 : DataFrame
        处理后的数据

    Example
    -------

    .. code-block:: python

        >>> import transbigdata as tbd
        >>> import pandas as pd
        #读取数据    
        >>> data = pd.read_csv('TaxiData-Sample.csv',header = None) 
        >>> data.columns = ['Vehicleid','Time','Lng','Lat','OpenStatus','Speed']      
        >>> data['Time'] = pd.to_datetime(data['Time'])
        #轨迹增密前的采样间隔
        >>> tbd.data_summary(data,col = ['Vehicleid','Time'],show_sample_duration=True)

        Amount of data
        
        Total number of data items:  544999
        Total number of individuals:  180
        Data volume of individuals(Mean):  3027.7722
        Data volume of individuals(Upper quartile):  4056.25
        Data volume of individuals(Median):  2600.5
        Data volume of individuals(Lower quartile):  1595.75

        Data time period
        
        Start time:  2022-06-29 00:00:00
        End time:  2022-06-29 23:59:59

        Sampling interval
        
        Mean:  27.995 s
        Upper quartile:  30.0 s
        Median:  20.0 s
        Lower quartile:  15.0 s

    进行轨迹增密，设置15秒一条数据::
        
        >>> data1 = tbd.traj_densify(data,timegap = 15)
        #轨迹增密后的采样间隔
        >>> tbd.data_summary(data1,show_sample_duration=True)

        Amount of data
        
        Total number of data items:  1526524
        Total number of individuals:  180
        Data volume of individuals(Mean):  8480.6889
        Data volume of individuals(Upper quartile):  9554.75
        Data volume of individuals(Median):  8175.0
        Data volume of individuals(Lower quartile):  7193.5

        Data time period
        
        Start time:  2022-06-29 00:00:00
        End time:  2022-06-29 23:59:59

        Sampling interval
        
        Mean:  9.992 s
        Upper quartile:  15.0 s
        Median:  11.0 s
        Lower quartile:  6.0 s

    增密后的效果

    .. image:: example-taxi/densify.png

    .. code-block:: python

        #两辆车的数据测试
        >>> tmp = data.iloc[:10]
        >>> tmp1 = data.iloc[-100:]
        >>> tmp = tmp.append(tmp1)

        #增密前数据
        >>> import geopandas as gpd
        >>> tmp['geometry'] = gpd.points_from_xy(tmp['Lng'],tmp['Lat'])
        >>> tmp = gpd.GeoDataFrame(tmp)
        >>> tmp[tmp['Vehicleid']==36805].plot()

        #进行轨迹增密，设置5秒一条数据
        >>> tmp1 = tbd.traj_densify(tmp,timegap = 1)
        >>> import geopandas as gpd
        >>> tmp1['geometry'] = gpd.points_from_xy(tmp1['Lng'],tmp1['Lat'])
        >>> tmp1 = gpd.GeoDataFrame(tmp1)
        >>> tmp1[tmp1['Vehicleid']==36805].plot()

        #轨迹稀疏化，20秒一条数据
        >>> tmp2 = tbd.traj_sparsify(tmp1,timegap = 20)
        >>> import geopandas as gpd
        >>> tmp2['geometry'] = gpd.points_from_xy(tmp2['Lng'],tmp2['Lat'])
        >>> tmp2 = gpd.GeoDataFrame(tmp2)
        >>> tmp2[tmp2['Vehicleid']==36805].plot()

    .. image:: example-taxi/sparsify.png
    '''
    pass


def points_to_traj(traj_points, col=['Lng', 'Lat', 'ID'], timecol=None):
    '''
    输入轨迹点，生成轨迹线型的GeoDataFrame

    Parameters
    -------
    traj_points : DataFrame
        轨迹点数据
    col : List
        列名，按[经度,纬度,轨迹编号]的顺序
    timecol : str
        可选，时间列的列名，如果给了则输出带有[经度,纬度,高度,时间]的geojson，可放入kepler中可视化轨迹

    Returns
    -------
    traj : GeoDataFrame或json
        生成的轨迹数据，如果timecol没定义则为GeoDataFrame，否则为json
    '''
    pass


def dumpjson(data, path):
    '''
    输入json数据，存储为文件。这个方法主要是解决numpy数值型无法兼容json包报错的问题

    Parameters
    -------
    data : json
        要储存的json数据
    path : str
        保存的路径
    '''
    pass