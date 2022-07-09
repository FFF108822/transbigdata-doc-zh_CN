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
    uid, timecol, lon, lat = col
    # Identify stay
    data = data.sort_values(by=col[:2])
    stay = data.copy()
    stay = stay.rename(columns={lon: 'lon', lat: 'lat', timecol: 'stime'})
    stay['stime'] = pd.to_datetime(stay['stime'])
    stay['LONCOL'], stay['LATCOL'] = GPS_to_grid(
        stay['lon'], stay['lat'], params)
    # Number the status
    stay['status_id'] = ((stay['LONCOL'] != stay['LONCOL'].shift()) |
                         (stay['LATCOL'] != stay['LATCOL'].shift()) |
                         (stay[uid] != stay[uid].shift())).astype(int)
    stay['status_id'] = stay.groupby([uid])['status_id'].cumsum()
    stay = stay.drop_duplicates(
        subset=[uid, 'status_id'], keep='first').copy()
    stay['etime'] = stay['stime'].shift(-1)
    stay = stay[stay[uid] == stay[uid].shift(-1)].copy()
    # Remove the duration shorter than given activitytime
    stay['duration'] = (pd.to_datetime(stay['etime']) -
                        pd.to_datetime(stay['stime'])).dt.total_seconds()
    stay = stay[stay['duration'] >= activitytime].copy()
    # Renumber the status
    stay['status_id'] = ((stay['LONCOL'] != stay['LONCOL'].shift()) |
                         (stay['LATCOL'] != stay['LATCOL'].shift()) |
                         (stay[uid] != stay[uid].shift())).astype(int)
    stay['status_id'] = stay.groupby([uid])['status_id'].cumsum()
    stay_stime = stay.drop_duplicates(subset=[uid, 'status_id'], keep='first')[
        [uid, 'stime', 'LONCOL', 'LATCOL', 'status_id']]
    stay_etime = stay.drop_duplicates(subset=[uid, 'status_id'], keep='last')[
        [uid, 'etime', 'LONCOL', 'LATCOL', 'status_id']]
    stay = pd.merge(stay_stime, stay_etime, how='left').drop(
        'status_id', axis=1)
    stay['lon'], stay['lat'] = grid_to_centre(
        [stay['LONCOL'], stay['LATCOL']], params)
    stay['duration'] = (pd.to_datetime(stay['etime']) -
                        pd.to_datetime(stay['stime'])).dt.total_seconds()
    # Identify move
    move = stay.copy()
    move['stime_next'] = move['stime'].shift(-1)
    move['elon'] = move['lon'].shift(-1)
    move['elat'] = move['lat'].shift(-1)
    move['ELONCOL'] = move['LONCOL'].shift(-1)
    move['ELATCOL'] = move['LATCOL'].shift(-1)
    move[uid+'_next'] = move[uid].shift(-1)
    move = move[move[uid+'_next'] == move[uid]
                ].drop(['stime', 'duration', uid+'_next'], axis=1)
    move = move.rename(columns={'lon': 'slon',
                                'lat': 'slat',
                                'etime': 'stime',
                                'stime_next': 'etime',
                                'LONCOL': 'SLONCOL',
                                'LATCOL': 'SLATCOL',
                                })
    move['duration'] = (
        move['etime'] - move['stime']).dt.total_seconds()
    return stay, move


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

    if (start_hour > end_hour) | (start_hour < 0) | (start_hour > 24) | (end_hour < 0) | (end_hour > 24):
        raise ValueError(
            'end_hour or start_hour error, it should be: 0 <= start_hour <= end_hour <= 24')

    night_hour = start_hour+24-end_hour
    day_hour = end_hour-start_hour
    stay = staydata.copy()
    stime, etime = col
    stay[stime] = pd.to_datetime(stay[stime])
    stay[etime] = pd.to_datetime(stay[etime])

    stay['preday'] = pd.to_datetime(
        stay[stime].dt.date)-pd.Timedelta(1, unit='days')+pd.Timedelta(end_hour, unit='hours')

    tmp = (stay[stime]-stay['preday']).dt.total_seconds()
    days = tmp//(24*3600)
    remain = tmp % (24*3600)
    duration_night_stime = days*night_hour*3600 + \
        np.min([remain, np.ones(len(tmp))*night_hour*3600], axis=0)
    duration_day_stime = days*day_hour*3600 + \
        np.max([remain-(night_hour*3600), np.zeros(len(tmp))], axis=0)

    tmp = (stay[etime]-stay['preday']).dt.total_seconds()
    days = tmp//(24*3600)
    remain = tmp % (24*3600)
    duration_night_etime = days*night_hour*3600 + \
        np.min([remain, np.ones(len(tmp))*night_hour*3600], axis=0)
    duration_day_etime = days*day_hour*3600 + \
        np.max([remain-(night_hour*3600), np.zeros(len(tmp))], axis=0)

    duration_night = duration_night_etime-duration_night_stime
    duration_day = duration_day_etime-duration_day_stime

    return duration_night, duration_day


def mobile_identify_home(staydata, col=['uid', 'stime', 'etime', 'LONCOL', 'LATCOL'], start_hour=8, end_hour=20):
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
    uid = col[0]
    stime = col[1]
    etime = col[2]
    stay = staydata.copy()
    if ('duration_night' not in stay.columns) | ('duration_day' not in stay.columns):
        stay['duration_night'], stay['duration_day'] = mobile_stay_dutation(
            stay, col=[stime, etime], start_hour=start_hour, end_hour=end_hour)
    # 夜晚最常停留地
    home = stay.groupby(
        [col[0], *col[3:]])['duration_night'].sum().reset_index()
    home = home.sort_values(by=[uid, 'duration_night'], ascending=False).drop_duplicates(
        subset=[uid], keep='first')
    home = home.drop(['duration_night'], axis=1)
    return home


def mobile_identify_work(staydata, col=['uid', 'stime', 'etime', 'LONCOL', 'LATCOL'], minhour=3, start_hour=8, end_hour=20, workdaystart=0, workdayend=4):
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
    uid = col[0]
    stime = col[1]
    etime = col[2]
    stay = staydata.copy()

    stay[stime] = pd.to_datetime(stay[stime])
    stay[etime] = pd.to_datetime(stay[etime])

    # 在工作日出现的日期数
    stay_workdays = stay[(stay[stime].dt.weekday >= workdaystart) &
                         (stay[stime].dt.weekday <= workdayend)].copy()

    # 将跨日的活动缩短为当日，以便计算日均持续时间
    stay_workdays['nextday'] = pd.to_datetime(
        stay_workdays[stime].dt.date+pd.Timedelta(1, unit='days'))
    stay_workdays[etime] = stay_workdays[[etime, 'nextday']].min(axis=1)
    stay_workdays['duration_night'], stay_workdays['duration_day'] = mobile_stay_dutation(
        stay_workdays, col=[stime, etime], start_hour=start_hour, end_hour=end_hour)

    # 白天最常活动地
    work = stay_workdays.groupby(
        [col[0], *col[3:]])['duration_day'].sum().reset_index()
    work = work.sort_values(by=[uid, 'duration_day'], ascending=False).drop_duplicates(
        subset=[uid], keep='first')

    # 人出现在多少个工作日
    stay_workdays['date'] = stay_workdays[stime].dt.date
    uid_workdays = stay_workdays[[uid, 'date']].drop_duplicates().groupby([uid])[
        'date'].count().reset_index()

    # 要求工作日每天平均minhour小时以上
    work = pd.merge(work, uid_workdays)
    work = work[(work['duration_day']/work['date']) >= minhour*3600].copy()
    work = work.drop(['duration_day', 'date'], axis=1)

    return work


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
    stime, etime, LONCOL, LATCOL = col
    activity = data.copy()
    activity['date'] = activity[stime].dt.date
    dates = list(activity['date'].astype(str).drop_duplicates())
    dates_all = []
    minday = min(dates)
    maxday = max(dates)
    import datetime
    thisdate = minday
    while thisdate != maxday:
        dates_all.append(thisdate)
        thisdate = str((pd.to_datetime(thisdate+' 00:00:00') +
                       datetime.timedelta(days=1)).date())
    dates = dates_all
    import matplotlib.pyplot as plt
    import numpy as np
    activity['duration'] = (activity[etime]-activity[stime]).dt.total_seconds()
    activity = activity[-activity['duration'].isnull()]
    import time
    activity['ststmp'] = activity[stime].astype(str).apply(
        lambda x: time.mktime(
            time.strptime(x, '%Y-%m-%d %H:%M:%S'))).astype('int64')
    activity['etstmp'] = activity[etime].astype(str).apply(
        lambda x: time.mktime(
            time.strptime(x, '%Y-%m-%d %H:%M:%S'))).astype('int64')
    activityinfo = activity[[LONCOL, LATCOL]].drop_duplicates()
    indexs = list(range(1, len(activityinfo)+1))
    np.random.shuffle(indexs)
    activityinfo['index'] = indexs
    import matplotlib as mpl
    norm = mpl.colors.Normalize(vmin=0, vmax=len(activityinfo))
    from matplotlib.colors import ListedColormap
    import seaborn as sns
    cmap = ListedColormap(sns.hls_palette(
        n_colors=len(activityinfo), l=.5, s=0.8))
    plt.figure(1, figsize, dpi)
    ax = plt.subplot(111)
    plt.sca(ax)
    for day in range(len(dates)):
        plt.bar(day, height=24*3600, bottom=0, width=0.4, color=(0, 0, 0, 0.1))
        stime = dates[day]+' 00:00:00'
        etime = dates[day]+' 23:59:59'
        bars = activity[(activity['stime'] < etime) &
                        (activity['etime'] > stime)].copy()
        bars['ststmp'] = bars['ststmp'] - \
            time.mktime(time.strptime(stime, '%Y-%m-%d %H:%M:%S'))
        bars['etstmp'] = bars['etstmp'] - \
            time.mktime(time.strptime(stime, '%Y-%m-%d %H:%M:%S'))
        for row in range(len(bars)):
            plt.bar(day,
                    height=bars['etstmp'].iloc[row]-bars['ststmp'].iloc[row],
                    bottom=bars['ststmp'].iloc[row],
                    color=cmap(
                        norm(
                            activityinfo[
                                (activityinfo[LONCOL] == bars[LONCOL].
                                 iloc[row]) &
                                (activityinfo[LATCOL] ==
                                 bars[LATCOL].iloc[row])
                            ]['index'].iloc[0])))
    plt.xlim(-0.5, len(dates))
    plt.ylim(0, 24*3600)
    plt.xticks(range(len(dates)), [i[-5:] for i in dates])
    plt.yticks(range(0, 24*3600+1, 3600),
               pd.DataFrame({'t': range(0, 25)})['t'].astype('str')+':00')
    plt.show()


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
