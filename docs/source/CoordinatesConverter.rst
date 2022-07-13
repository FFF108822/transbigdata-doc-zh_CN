.. _CoordinatesConverter:
.. currentmodule:: transbigdata

******************************
坐标距离
******************************

方法总览
-------------

.. autosummary::
    
    gcj02tobd09
    gcj02towgs84
    wgs84togcj02
    wgs84tobd09
    bd09togcj02
    bd09towgs84
    bd09mctobd09
    transform_shape
    getdistance

火星坐标系互转
-------------


坐标互转方法
=============================

TransBigData包提供了GCJ02,BD09,BD09mc,WGS94坐标系互转。



.. autofunction:: gcj02tobd09

.. autofunction:: bd09togcj02

.. autofunction:: wgs84togcj02

.. autofunction:: gcj02towgs84

.. autofunction:: wgs84tobd09

.. autofunction:: bd09towgs84

.. autofunction:: bd09mctobd09

坐标互转，基于numpy列运算::

  >>> data['Lng'],data['Lat'] = tbd.wgs84tobd09(data['Lng'],data['Lat'])  
  >>> data['Lng'],data['Lat'] = tbd.wgs84togcj02(data['Lng'],data['Lat'])  
  >>> data['Lng'],data['Lat'] = tbd.gcj02tobd09(data['Lng'],data['Lat'])  
  >>> data['Lng'],data['Lat'] = tbd.gcj02towgs84(data['Lng'],data['Lat'])  
  >>> data['Lng'],data['Lat'] = tbd.bd09togcj02(data['Lng'],data['Lat'])  
  >>> data['Lng'],data['Lat'] = tbd.bd09towgs84(data['Lng'],data['Lat'])  
  >>> data['Lng'],data['Lat'] = tbd.bd09mctobd09(data['Lng'],data['Lat']) 

对地理要素整体转换坐标
=============================

.. autofunction:: transform_shape


经纬度计算距离
-------------

.. autofunction:: getdistance