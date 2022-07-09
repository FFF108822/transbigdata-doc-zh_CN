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


def bikedata_to_od(data,
                   col=['BIKE_ID', 'DATA_TIME', 'LONGITUDE',
                        'LATITUDE', 'LOCK_STATUS'],
                   startend=None):
    '''
    输入共享单车订单数据（只在开关锁时产生数据），指定列名，提取其中的骑行与停车信息

    Parameters
    -------
    data : DataFrame
        共享单车订单数据，只在开关锁时产生数据
    col : List
        列名，顺序不能变，分别为[单车ID,时间,经度,纬度,锁状态]，例如['BIKE_ID','DATA_TIME','LONGITUDE','LATITUDE','LOCK_STATUS']
    startend : List
        传入的为[开始时间,结束时间]，如['2018-08-27 00:00:00','2018-08-28 00:00:00']。
        如传入，则考虑（观测时段开始时到单车第一次出现）与（单车最后一次出现到观测时段结束）的骑行与停车情况。
        
    Returns
    -------
    move_data : DataFrame
        骑行订单数据
    stop_data : DataFrame
        停车数据
    '''
    [BIKE_ID, DATA_TIME, LONGITUDE, LATITUDE, LOCK_STATUS] = col
    oddata = data.copy()
    oddata = oddata.sort_values(by=[BIKE_ID, DATA_TIME])
    if startend:
        oddata['tmp_index'] = range(len(oddata))
        # Add records at the beginning of the time period
        data_1 = oddata.copy()
        # After grouping the single vehicle ID, sort it in ascending order
        # according to time to get the rank id
        data_1['rank'] = data_1.groupby(
            BIKE_ID)['tmp_index'].rank(method='first')
        data_1 = data_1[data_1['rank'] == 1]
        # Modify time to the start time of the observation period
        data_1[DATA_TIME] = startend[0]
        data_1[LOCK_STATUS] = 1
        # Add records at the end of the time period
        data_2 = oddata.copy()
        data_2['rank'] = data_2.groupby(BIKE_ID)['tmp_index'].rank(
            ascending=False, method='first')
        data_2 = data_2[data_2['rank'] == 1]
        data_2[DATA_TIME] = startend[1]
        data_2[LOCK_STATUS] = 0
        oddata = pd.concat([oddata, data_1, data_2]).sort_values(
            by=[BIKE_ID, DATA_TIME])
    for i in col:
        oddata[i+'_'] = oddata[i].shift(-1)
    oddata = oddata[oddata[BIKE_ID] == oddata[BIKE_ID+'_']]
    move_data = oddata[(oddata[LOCK_STATUS] == 0) &
                       (oddata[LOCK_STATUS+'_'] == 1)][[
                           BIKE_ID, DATA_TIME, LONGITUDE, LATITUDE,
                           DATA_TIME+'_', LONGITUDE+'_', LATITUDE+'_']]
    move_data.columns = [BIKE_ID, 'stime',
                         'slon', 'slat', 'etime', 'elon', 'elat']
    stop_data = oddata[(oddata[LOCK_STATUS] == 1) &
                       (oddata[LOCK_STATUS+'_'] == 0)][[
                           BIKE_ID, DATA_TIME, LONGITUDE, LATITUDE,
                           DATA_TIME+'_', LONGITUDE+'_', LATITUDE+'_']]
    stop_data.columns = [BIKE_ID, 'stime',
                         'slon', 'slat', 'etime', 'elon', 'elat']
    return move_data, stop_data
