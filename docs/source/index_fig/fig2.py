import transbigdata as tbd
#读取数据    
import pandas as pd
data = pd.read_csv('../../../example/data/TaxiData-Sample.csv',header = None) 
data.columns = ['VehicleNum','time','lon','lat','OpenStatus','Speed'] 
#定义研究范围
bounds = [113.75, 22.4, 114.62, 22.86]
#剔除研究范围外的数据
data = tbd.clean_outofbounds(data,bounds = bounds,col = ['lon','lat'])
#获取栅格化参数
params = tbd.area_to_params(bounds,accuracy = 1000)
#设置为六边形网格
params['method'] = 'hexa'
#设置为三角形网格: params['method'] = 'tri'
#设置旋转角度，单位为度
params['theta'] = 5
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