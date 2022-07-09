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


def sample_duration(data, col=['Vehicleid', 'Time']):
    '''
    统计数据采样间隔

    Parameters
    -------
    data : DataFrame
        数据
    col : List
        列名，按[个体ID,时间]的顺序

    Returns
    -------
    sample_duration : DataFrame
        一列的数据表，列名为duration，内容是数据的采样间隔，单位秒
    '''
    [Vehicleid, Time] = col
    data1 = data.copy()
    data1[Time] = pd.to_datetime(data1[Time])
    data1 = data1.sort_values(by=[Vehicleid, Time])
    data1[Vehicleid+'1'] = data1[Vehicleid].shift(-1)
    data1[Time+'1'] = data1[Time].shift(-1)
    data1['duration'] = (data1[Time+'1']-data1[Time]).dt.total_seconds()
    data1 = data1[data1[Vehicleid+'1'] == data1[Vehicleid]]
    sample_duration = data1[['duration']]
    return sample_duration



def data_summary(data, col=['Vehicleid', 'Time'], show_sample_duration=False,
                 roundnum=4):
    '''
    输入数据，打印数据概况

    Parameters
    -------
    data : DataFrame
        轨迹点数据
    col : List
        列名，按[个体ID，时间]的顺序
    show_sample_duration : bool
        是否输出个体采样间隔信息
    roundnum : number
        小数点取位数

    Example
    -----------------
    使用方法

    .. code-block:: python

        >>> tbd.data_summary(data,
        ...                  col = ['Vehicleid','Time'],
        ...                  show_sample_duration=True)
        
        Amount of data
        
        Total number of data items:  544999
        Total number of individuals:  180
        Data volume of individuals(Mean):  3027.7722
        Data volume of individuals(Upper quartile):  4056.25
        Data volume of individuals(Median):  2600.5
        Data volume of individuals(Lower quartile):  1595.75

        Data time period
        
        Start time:  2022-01-09 00:00:00
        End time:  2022-01-09 23:59:59

        Sampling interval
        
        Mean:  27.995 s
        Upper quartile:  30.0 s
        Median:  20.0 s
        Lower quartile:  15.0 s
    '''
    [Vehicleid, Time] = col
    print('Amount of data')
    print('-----------------')
    print('Total number of data items: ', len(data))
    Vehicleid_count = data[Vehicleid].value_counts()
    print('Total number of individuals: ', len(Vehicleid_count))
    print('Data volume of individuals(Mean): ',
          round(Vehicleid_count.mean(), roundnum))
    print('Data volume of individuals(Upper quartile): ',
          round(Vehicleid_count.quantile(0.75), roundnum))
    print('Data volume of individuals(Median): ', round(
        Vehicleid_count.quantile(0.5), roundnum))
    print('Data volume of individuals(Lower quartile): ',
          round(Vehicleid_count.quantile(0.25), roundnum))
    print('')
    print('Data time period')
    print('-----------------')
    print('Start time: ', data[Time].min())
    print('End time: ', data[Time].max())
    print('')
    if show_sample_duration:
        sd = sample_duration(data, col=[Vehicleid, Time])
        print('Sampling interval')
        print('-----------------')
        print('Mean: ', round(sd['duration'].mean(), roundnum), 's')
        print('Upper quartile: ', round(
            sd['duration'].quantile(0.75), roundnum), 's')
        print('Median: ', round(sd['duration'].quantile(0.5), roundnum), 's')
        print('Lower quartile: ', round(
            sd['duration'].quantile(0.25), roundnum), 's')