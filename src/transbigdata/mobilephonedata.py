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
from .grids import GPS_to_grid, grid_to_centre


def mobile_stay_move(data, params,
                     col=['ID', 'dataTime', 'longitude', 'latitude'],
                     activitytime=1800):
    '''
    输入轨迹数据与栅格化参数，识别活动与出行

    Parameters
    ----------------
    data : DataFrame
        轨迹数据集
    params : List
        栅格化参数
    col : List
        数据的列名[个体，时间，经度，纬度]顺序
    activitytime : Number
        多长时间识别为停留

    Returns
    ----------------
    stay : DataFrame
        个体停留信息
    move : DataFrame
        个体移动信息
    '''


def mobile_stay_dutation(staydata, col=['stime', 'etime'], start_hour=8, end_hour=20):
    '''
    输入停留点数据，识别白天与夜晚的持续时间

    Parameters
    ----------------
    staydata : DataFrame
        停留点数据
    col : List
        列名，顺序为 ['starttime','endtime']
    start_hour,end_hour : Number
        白天开始与白天结束时间（小时）

    Returns
    ----------------
    duration_night : Series
        夜晚停留时间列（时长总和）
    duration_day : Series
        白天停留时间列（时长总和）
    '''


def mobile_identify_home(staydata, col=['uid','stime', 'etime','LONCOL', 'LATCOL'], start_hour=8, end_hour=20 ):
    '''
    输入停留点数据识别居住地。规则为夜晚时段停留最长地点。

    Parameters
    ----------------
    staydata : DataFrame
        停留点数据
    col : List
        列名，顺序为 ['uid','stime', 'etime', 'locationtag1', 'locationtag2', ...].
        可由多个'locationtag'列指定一个地点
    start_hour, end_hour : Number
        白天开始与白天结束时间（小时）

    Returns
    ----------------
    home : DataFrame
        居住地位置
    '''


def mobile_identify_work(staydata, col=['uid', 'stime', 'etime', 'LONCOL', 'LATCOL'], minhour=3, start_hour=8, end_hour=20,workdaystart=0, workdayend=4):
    '''
    输入停留点数据识别工作地。规则为工作日白天时段停留最长地点（每日平均时长大于`minhour`）。

    Parameters
    ----------------
    staydata : DataFrame
        停留点数据
    col : List
        列名，顺序为 ['uid','stime', 'etime', 'locationtag1', 'locationtag2', ...].
        可由多个'locationtag'列指定一个地点
    minhour : Number
        每日平均时长大于`minhour`(小时).
    workdaystart,workdayend : Number
        一周中工作日. 0 - Monday, 4 - Friday
    start_hour, end_hour : Number
        白天开始与白天结束时间（小时）


    Returns
    ----------------
    work : DataFrame
        工作地位置
    '''


def mobile_plot_activity(data, col=['stime', 'etime', 'LONCOL', 'LATCOL'],
                         figsize=(10, 5), dpi=250):
    '''
    输入个体的活动数据（单一个体），绘制活动图

    Parameters
    ----------------
    data : DataFrame
        活动数据集
    col : List
        列名，分别为[活动开始时间，活动结束时间，活动所在栅格经度编号，活动所在栅格纬度编号]
    '''
  
'''Old namespace'''

def traj_stay_move(data, params,
                     col=['ID', 'dataTime', 'longitude', 'latitude'],
                     activitytime=1800):
    '''
    .. note::
        该方法已经更名为 :func:`transbigdata.mobile_stay_move`，旧方法名称依然可以使用。


    '''

def plot_activity(data, params,
                     col=['ID', 'dataTime', 'longitude', 'latitude'],
                     activitytime=1800):
    '''
    .. note::
        该方法已经更名为 :func:`transbigdata.mobile_plot_activity`，旧方法名称依然可以使用。
    
    '''