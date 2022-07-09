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


def clean_taxi_status(data, col=['VehicleNum', 'Time', 'OpenStatus'],
                      timelimit=None):
    '''
    删除出租车数据中载客状态瞬间变化的记录，这些记录的存在会影响出行订单判断。
    判断条件为:如果对同一辆车，上一条记录与下一条记录的载客状态都与本条记录不同，则本条记录应该删去

    Parameters
    -------
    data : DataFrame
        数据
    col : List
        列名，按[车辆ID,时间,载客状态]的顺序
    timelimit : number
        可选，单位为秒，上一条记录与下一条记录的时间小于该时间阈值才予以删除

    Returns
    -------
    data1 : DataFrame
        清洗后的数据
    '''
    data1 = data.copy()
    [VehicleNum, Time, OpenStatus] = col
    if timelimit:
        data1[Time] = pd.to_datetime(data1[Time])
        data1 = data1[
            -((data1[OpenStatus].shift(-1) == data1[OpenStatus].shift()) &
              (data1[OpenStatus] != data1[OpenStatus].shift()) &
              (data1[VehicleNum].shift(-1) == data1[VehicleNum].shift()) &
              (data1[VehicleNum] == data1[VehicleNum].shift()) &
              ((data1[Time].shift(-1) - data1[Time].shift()
                ).dt.total_seconds() <= timelimit)
              )]
    else:
        data1 = data1[
            -((data1[OpenStatus].shift(-1) == data1[OpenStatus].shift()) &
              (data1[OpenStatus] != data1[OpenStatus].shift()) &
              (data1[VehicleNum].shift(-1) == data1[VehicleNum].shift()) &
              (data1[VehicleNum] == data1[VehicleNum].shift()))]
    return data1



def taxigps_to_od(data,
                  col=['VehicleNum', 'Stime', 'Lng', 'Lat', 'OpenStatus']):
    '''
    出租车OD提取算法，输入出租车GPS数据,提取OD

    Parameters
    -------
    data : DataFrame
        出租车GPS数据（清洗好的）
    col : List            
        数据中各列列名，需要按顺序[车辆id，时间，经度，纬度，载客状态]

    Returns
    -------
    oddata : DataFrame
        OD数据
    '''
    [VehicleNum, Stime, Lng, Lat, OpenStatus] = col
    data1 = data[col]
    data1 = data1.sort_values(by=[VehicleNum, Stime])
    data1['StatusChange'] = data1[OpenStatus] - data1[OpenStatus].shift()
    oddata = data1[((data1['StatusChange'] == -1) |
                   (data1['StatusChange'] == 1)) &
                   (data1[VehicleNum].shift() == data1[VehicleNum])]
    oddata = oddata.drop([OpenStatus], axis=1)
    oddata.columns = [VehicleNum, 'stime', 'slon', 'slat', 'StatusChange']
    oddata['etime'] = oddata['stime'].shift(-1)
    oddata['elon'] = oddata['slon'].shift(-1)
    oddata['elat'] = oddata['slat'].shift(-1)
    oddata = oddata[(oddata['StatusChange'] == 1) &
                    (oddata[VehicleNum] == oddata[VehicleNum].shift(-1))]
    oddata = oddata.drop('StatusChange', axis=1)
    oddata['ID'] = range(len(oddata))
    return oddata



def taxigps_traj_point(data, oddata,
                       col=['Vehicleid', 'Time', 'Lng', 'Lat', 'OpenStatus']):
    '''
    输入出租车数据与OD数据，提取载客与空载的行驶路径点

    Parameters
    -------
    data : DataFrame
        出租车GPS数据，字段名由col变量指定
    oddata : DataFrame
        出租车OD数据
    col : List
        列名，按[车辆ID,时间,经度,纬度,载客状态]的顺序

    Returns
    -------
    data_deliver : DataFrame
        载客轨迹点
    data_idle : DataFrame
        空载轨迹点
    '''
    VehicleNum, Time, Lng, Lat, OpenStatus = col
    oddata1 = oddata.copy()
    odata = oddata1[[VehicleNum, 'stime', 'slon', 'slat', 'ID']].copy()
    odata.columns = [VehicleNum, Time, Lng, Lat, 'ID']
    odata.loc[:, 'flag'] = 1
    odata.loc[:, OpenStatus] = -1
    ddata = oddata1[[VehicleNum, 'etime', 'elon', 'elat', 'ID']].copy()
    ddata.columns = [VehicleNum, Time, Lng, Lat, 'ID']
    ddata.loc[:, 'flag'] = -1
    ddata.loc[:, OpenStatus] = -1
    data1 = pd.concat([data, odata, ddata])
    data1 = data1.sort_values(by=[VehicleNum, Time, OpenStatus])
    data1['flag'] = data1['flag'].fillna(0)
    data1['flag'] = data1.groupby(VehicleNum)['flag'].cumsum()
    data1['ID'] = data1['ID'].ffill()
    data_deliver = data1[(data1['flag'] == 1) &
                         (-data1['ID'].isnull()) & (data1[OpenStatus] != -1)]
    data_idle = data1[(data1['flag'] == 0) &
                      (-data1['ID'].isnull()) & (data1[OpenStatus] != -1)]
    return data_deliver, data_idle
