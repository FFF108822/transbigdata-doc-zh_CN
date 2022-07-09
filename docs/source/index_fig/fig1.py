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
#将GPS数据对应至栅格
data['LONCOL'],data['LATCOL'] = tbd.GPS_to_grid(data['lon'],data['lat'],params)
#聚合集计栅格内数据量
grid_agg = data.groupby(['LONCOL','LATCOL'])['VehicleNum'].count().reset_index()
#生成栅格的几何图形
grid_agg['geometry'] = tbd.grid_to_polygon([grid_agg['LONCOL'],grid_agg['LATCOL']],params)
#转换为GeoDataFrame
import geopandas as gpd
grid_agg = gpd.GeoDataFrame(grid_agg)
#绘制栅格
grid_agg.plot(column = 'VehicleNum',cmap = 'autumn_r')