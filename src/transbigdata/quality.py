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
    pass


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
    pass