.. transbigdata documentation master file, created by
   sphinx-quickstart on Thu Oct 21 14:41:25 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

TransBigData 为交通时空大数据而生
========================================

.. image:: _static/logo-wordmark-dark.png



**主要功能**

TransBigData工具针对时空大数据处理而开发，依托于GeoPandas。TransBigData集成了交通时空大数据处理过程中常用的方法。包括栅格化、数据质量分析、数据预处理、数据集计、轨迹分析、GIS处理、地图底图加载、坐标与距离计算、数据可视化等通用方法。TransBigData也针对出租车GPS数据、共享单车数据、公交GPS数据等多种常见交通时空大数据提供了快速简洁的处理方法。

**技术特点**

* 面向交通时空大数据分析不同阶段的处理需求提供不同处理功能。
* 代码简洁、高效、灵活、易用，通过简短的代码即可实现复杂的数据任务。


TransBigData简介
==============================

快速入门
---------------

| 在安装TransBigData之前，请确保已经安装了可用的geopandas包：https://geopandas.org/index.html
| 如果你已经安装了geopandas，则直接在命令提示符中运行下面代码即可安装

::

    pip install -U transbigdata

下面例子展示如何使用TransBigData工具快速地从出租车GPS数据中提取出行OD

::

    #导入TransBigData包
    import transbigdata as tbd
    #读取数据    
    import pandas as pd
    data = pd.read_csv('data/TaxiData-Sample.csv',header = None) 
    data.columns = ['VehicleNum','time','lon','lat','OpenStatus','Speed'] 
    data


首先定义研究范围，并使用 :func:`transbigdata.clean_outofbounds` 剔除研究范围外的数据

::

   #定义研究范围
   bounds = [113.75, 22.4, 114.62, 22.86]
   #剔除研究范围外的数据
   data = tbd.clean_outofbounds(data,bounds = bounds,col = ['lon','lat'])
   

以栅格形式表达数据分布是最基本的表达方法。GPS数据经过栅格化后，每个数据点都含有对应的栅格信息，采用栅格表达数据的分布时，其表示的分布情况与真实情况接近。如果要使用 TransBigData工具进行栅格划分，首先需要确定栅格化的参数（可以理解为定义了一个栅格坐标系），参数可以帮助我们快速进行栅格化:

::

   #获取栅格化参数
   params = tbd.area_to_params(bounds,accuracy = 1000)
   params

取得栅格化参数后，将GPS对应至栅格。使用 :func:`transbigdata.GPS_to_grid` 方法,该方法会生成 LONCOL列与 LATCOL列，并由这两列共同指定一个栅格:

::

   #将GPS数据对应至栅格
   data['LONCOL'],data['LATCOL'] = tbd.GPS_to_grid(data['lon'],data['lat'],params)
   data

聚合集计栅格内数据量，并为栅格生成几何图形：

::

   #聚合集计栅格内数据量
   grid_agg = data.groupby(['LONCOL','LATCOL'])['VehicleNum'].count().reset_index()
   #生成栅格的几何图形
   grid_agg['geometry'] = tbd.grid_to_polygon([grid_agg['LONCOL'],grid_agg['LATCOL']],params)
   #转换为GeoDataFrame
   import geopandas as gpd
   grid_agg = gpd.GeoDataFrame(grid_agg)
   #绘制栅格
   grid_agg.plot(column = 'VehicleNum',cmap = 'autumn_r')

.. plot:: index_fig/fig1.py

TransBigData支持三角形、六边形网格，也支持为网格赋予旋转角度。我们可以通过以下方式改变栅格参数来进行设定

::

   #设置为六边形网格
   params['method'] = 'hexa'
   #设置为三角形网格: params['method'] = 'tri'
   #设置旋转角度，单位为度
   params['theta'] = 5
   params

然后我们可以再次进行匹配、集计:

::

   #三角形和六边形网格要求三列存储栅格ID信息
   data['loncol_1'],data['loncol_2'],data['loncol_3'] = tbd.GPS_to_grid(data['lon'],data['lat'],params)
   #聚合集计栅格内数据量
   grid_agg = data.groupby(['loncol_1','loncol_2','loncol_3'])['VehicleNum'].count().reset_index()
   #生成栅格的几何图形
   grid_agg['geometry'] = tbd.grid_to_polygon([grid_agg['loncol_1'],grid_agg['loncol_2'],grid_agg['loncol_3']],params)
   #转换为GeoDataFrame
   import geopandas as gpd
   grid_agg = gpd.GeoDataFrame(grid_agg)
   #绘制栅格
   grid_agg.plot(column = 'VehicleNum',cmap = 'autumn_r')

.. plot:: index_fig/fig2.py

使用示例
---------------
.. raw:: html
   :file: gallery/html/grid.html


相关链接
---------------

* 小旭学长的b站： https://space.bilibili.com/3051484
* 小旭学长的七天入门交通时空大数据分析课程（零基础免费课）： https://www.lifangshuju.com/#/introduce/166  
* 小旭学长的交通时空大数据分析课程： https://www.lifangshuju.com/#/introduce/154  
* 小旭学长的数据可视化课程： https://www.lifangshuju.com/#/introduce/165  
* 本项目的github页面： https://github.com/ni1o1/transbigdata/  
* 有bug请在这个页面提交： https://github.com/ni1o1/transbigdata/issues

安装
=========================

.. toctree::
   :caption: 安装
   :maxdepth: 2
   
   getting_started.rst


使用示例
=========================

.. toctree::
   :caption: 使用示例
   :maxdepth: 2

   gallery/index.rst
   example-taxi/example-taxi.rst
   example-busgps/example-busgps.rst
   metromodel/metromodel.rst
   Example-pNEUMA/Example-pNEUMA.rst
   example-bikesharing/example-bikesharing.rst
   Example-Mobile/Example-Mobile.rst
   
通用方法
=========================

.. toctree::
   :caption: 通用方法
   :maxdepth: 2
   
   quality.rst
   preprocess.rst
   grids.rst
   odprocess.rst
   visualization.rst
   getbusdata.rst
   traj.rst
   gisprocess.rst
   plot_map.rst
   CoordinatesConverter.rst
   utils.rst


各类数据处理方法
=========================

.. toctree::
   :caption: 各类数据处理方法
   :maxdepth: 2

   mobile.rst
   taxigps.rst
   bikedata.rst
   busgps.rst
   metroline.rst



