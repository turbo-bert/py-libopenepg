import openepg
from pprint import pprint as PP

#print(openepg.list_channels())
#print(openepg.generate_forecast_dates_de())
#print(openepg.generate_forecast_dates_iso())
#print(openepg.get_cachedir())
#print(openepg.get_conf_lines())
#PP(openepg.get_conf())


openepg.run_update()
