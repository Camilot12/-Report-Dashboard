# -*- coding: utf-8 -*-
from pathlib import Path # Python standard library
import pandas as pd # pip install pandas openpyxl
from taipy.gui import Gui, notify
#import taipy.gui.builder as tgb
import calendar 
#---------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCIONES -------------------------------------------------------------------------------------------------------------
def on_dropdown_change(state):
    notify(state, "info", f"The text is: {state.text}")
    # https://docs.taipy.io/en/release-2.4/getting_started/getting-started-gui/step_04/ReadMe/
#    on_change(state, "year", state.text)
def on_change(state, var_name, var_value):
    #print("entró", var_name)
    global filtered_ventas_max_mes_año
    if var_name == "year":
        state.data = var_value
        state.text1 = ventas_por_año_mes[int(state.data)][mes_max_ventas_año[int(state.data)]]
        state.text4 = ventas_por_año_mes[int(state.data)][mes_min_ventas_año[int(state.data)]]
        state.text3 = vendedor_max_clientes_por_año[vendedor_max_clientes_por_año["año"] == int(state.data)]["Nom_Completo_Vendedor"].iloc[0]
        state.text2 = crecimiento_ventas_anual[int(state.data)].round(2)
        state.text5 = (str(trimestre_menor_rentabilidad_por_año[int(state.data)]).split('Q')[1])[0]
#---------------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------- ARREGLAR DATOS -------------------------------------------------------------------------------------------------------------
# Guardamos los valores del archivo Vendedor.txt en la variable vendedor
vendedor = pd.read_csv("Vendedor.txt", sep="\t") 
# Guardamos los valores del archivo Departamento.txt en la variable departamento
# Arreglamos los valores "Departamento - Clave" convertimos de objeto a string los valores
departamento = pd.read_csv("Departamento.txt", sep="\t", dtype={"Departamento - Clave":str})
# Guardamos los valores del archivo BD.csv en la variable BD
BD = pd.read_csv("BD.csv", encoding="latin1", dtype={"Departamento - Clave":str})
# Arreglamos los nombres de las columnas Número de Vendedor y Número de Cliente
BD = BD.rename(columns={"N£mero de Vendedor":"Número de Vendedor"})
BD = BD.rename(columns={"N£mero de cliente":"Número de Cliente"})
usd_quetzal = 7.5 # 1USD:7.5Q
BD["Ventas Netas (Q)"] = BD["Ventas Netas (Q)"].apply(lambda x: x / usd_quetzal).round(2)
BD["Costo"]=BD["Costo"].apply(lambda x: x / usd_quetzal).round(2)
BD=BD.rename(columns={"Ventas Netas (Q)":"Ventas Netas (USD)", "Costo":"Costo (USD)"})
# Eliminamos columnas vacias
BD=BD.drop(columns=["Unnamed: 2", "Unnamed: 12", "Unnamed: 13"]) #Borrar Columnas
# Eliminamos filas nulas
condition = ~BD.isna().all(axis=1) #Borrar Filas Vacias
BD=BD[condition].copy().reset_index(drop=True)
# Corregimos el tipo de celda en la base de datos
BD["Número de Vendedor"]=BD["Número de Vendedor"].astype(int)
BD["Número de Cliente"]=BD["Número de Cliente"].astype(int)
BD["Familia - Clave"]=BD["Familia - Clave"].astype(int)
BD["Nom_Completo_Vendedor"]=BD["Nom_Completo_Vendedor"].astype(str)
BD["Fecha"] = pd.to_datetime(BD["Fecha"])
# Extraer el mes, año y  Trimestre de cada Fecha
BD["mes"] = BD["Fecha"].dt.month
BD["año"] = BD["Fecha"].dt.year
BD["Trimestre"] = BD["Fecha"].dt.to_period("Q")
# Ahora vamos a poblar los datos faltantes
# Agregar nombre del vendedor
vendedor["Nombre Completo"] = vendedor["Nombre"]+" "+vendedor["Apellido"] # Creamos una nueva columna "Nombre Completo" a partir de las comunas "Nombre" y "Apellido" del DF vendedor
BD=BD.merge(vendedor, left_on="Número de Vendedor", right_on="No. Vendedor") # Agregamos el nombre completo del vendedor a la base de datos comando la clave de cada DF 
BD["Nom_Completo_Vendedor"]=BD["Nombre Completo"] # Ahora igualamos la columnas para el nombre completo quede en la columna que deseamos
departamentoAlias={} # Diccionario para poblar los nombres por departamento
departamentoAliasInverse={} # Diccionario para poblar las Claves por departamento
for row in departamento.iterrows():
  data = row[1]
  key=data["Departamento - Clave"]
  value=data["Departamento"]
  departamentoAlias[key]=value
  departamentoAliasInverse[value]=key
BD["Departamento Replace"]=BD["Departamento - Clave"].replace(departamentoAlias).fillna(BD["Departamento"]) # Creamos la columa "Departamento Replace" para fusionar con la columa "Departamentos"
# Por ultimo fusionamos las columnas creadas con las columnas que queremos poblar los valores
BD["Departamento Replace"]=BD["Departamento Replace"].replace({"Plomer¡a":"Plomería"}) # Arreglamos celdas que tenian escrito mal el nombre
BD["Departamento"]=BD["Departamento Replace"]
BD["Departamento - Clave Replace"]=BD["Departamento"].replace(departamentoAliasInverse).fillna(BD["Departamento - Clave"])
BD["Departamento - Clave"] = BD["Departamento - Clave Replace"]
# BD[["Departamento - Clave","Departamento"]].value_counts()
# Verifico que se colocaron correctamente los valores
# Borrar columnas innecesarias
columnas_a_borrar=["No. Vendedor", "Nombre", "Apellido", "Nombre Completo", "Departamento Replace", "Departamento - Clave Replace"]
BD =BD.drop(columnas_a_borrar, axis=1)
print(BD.dtypes)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------- RESPUESTAS -------------------------------------------------------------------------------------------------------------
# 1. & 2.  ---------------------------------------------------------------------------------------
# Agrupar por producto y sumar las ventas
departamento_abc = BD.groupby("Departamento")["Ventas Netas (USD)"].sum().reset_index()
# Ordenar por ventas de mayor a menor
departamento_abc = departamento_abc.sort_values(by="Ventas Netas (USD)", ascending=False)
# Calcular el porcentaje acumulado de ventas
departamento_abc["Porcentaje %"] = departamento_abc["Ventas Netas (USD)"].cumsum() / departamento_abc["Ventas Netas (USD)"].sum() * 100
#print(departamento_abc)
# Clasificar los productos en categorías A, B y C
clase_a = departamento_abc[departamento_abc["Porcentaje %"] <= 80]["Departamento"].tolist()
clase_a_ventas = departamento_abc[departamento_abc["Porcentaje %"] <= 80]["Ventas Netas (USD)"].cumsum().iloc[-1].round(2)
grupo_a = departamento_abc["Departamento"].isin(clase_a)
grupo_a = departamento_abc.loc[grupo_a, ["Departamento", "Ventas Netas (USD)"]]
grupo_a = grupo_a.reset_index(drop=True)
print(grupo_a)

clase_b = departamento_abc[(departamento_abc["Porcentaje %"] > 80) & (departamento_abc["Porcentaje %"] <= 95)]["Departamento"].tolist()
clase_b_ventas = departamento_abc[(departamento_abc["Porcentaje %"] > 80) & (departamento_abc["Porcentaje %"] <= 95)]["Ventas Netas (USD)"].cumsum().iloc[-1].round(2)
grupo_b = departamento_abc["Departamento"].isin(clase_b)
grupo_b = departamento_abc.loc[grupo_b, ["Departamento", "Ventas Netas (USD)"]]
grupo_b = grupo_b.reset_index(drop=True)
print(grupo_b)

clase_c = departamento_abc[departamento_abc["Porcentaje %"] > 95]["Departamento"].tolist()
clase_c_ventas = departamento_abc[departamento_abc["Porcentaje %"] > 95]["Ventas Netas (USD)"].cumsum().iloc[-1].round(2)
grupo_c = departamento_abc["Departamento"].isin(clase_c)
grupo_c = departamento_abc.loc[grupo_c, ["Departamento", "Ventas Netas (USD)"]]
grupo_c = grupo_c.reset_index(drop=True)
print(grupo_c)

# Imprimir los resultados
#print("Clase A (80% de las ventas):")
#print(clase_a)
#print(len(clase_a))
#print(clase_a_ventas)

#print("\nClase B (15% de las ventas):")
#print(clase_b)
#print(len(clase_b))
#print(clase_b_ventas)

#print("\nClase C (5% de las ventas):")
#print(clase_c)
#print(len(clase_c))
#print(clase_c_ventas)

# 3. ABC de clientes  ---------------------------------------------------------------------------------------
# Agrupar por cliente y sumar las ventas
cliente_abc = BD.groupby("Número de Cliente")["Ventas Netas (USD)"].sum().reset_index()

# Ordenar por ventas de mayor a menor
cliente_abc = cliente_abc.sort_values(by="Ventas Netas (USD)", ascending=False)

# Calcular el porcentaje acumulado de ventas
cliente_abc["Porcentaje %"] = cliente_abc["Ventas Netas (USD)"].cumsum() / cliente_abc["Ventas Netas (USD)"].sum() * 100

cliente_abc["Clase"] = ["A" if p <= 80 else "B" if p <= 95 else "C" for p in cliente_abc["Porcentaje %"]]

top_clientes = cliente_abc[cliente_abc["Clase"] == 'A'].head(5)["Número de Cliente"].tolist()
#print(top_clientes)

# 4. Identificar vendedor con mas clientes  ---------------------------------------------------------------------------------------
# Contar el número de ventas por vendedor y cliente
ventas_por_vendedor_cliente = BD.groupby(["Nom_Completo_Vendedor", "Número de Cliente", "año"]).size().reset_index(name="Número de Ventas")

# Obtener el vendedor que tiene más clientes por año
vendedor_max_clientes_por_año = ventas_por_vendedor_cliente.loc[ventas_por_vendedor_cliente.groupby("año")["Número de Cliente"].idxmax(), ["Nom_Completo_Vendedor", "año"]]

#print(vendedor_max_clientes_por_año)

# 5. MES CON MAS VENTAS PARA EL AÑO 2015 Y 2016 ---------------------------------------------------------------------------------------
# Agrupar por mes y sumar las Ventas Netas (USD)
ventas_por_año_mes = BD.groupby(["año", "mes"])["Ventas Netas (USD)"].sum()

# Agrupar por mes y sumar los Costo (USD)
costos_por_año_mes = BD.groupby(["año", "mes"])["Costo (USD)"].sum()

# Mes con mayor ventas para cada año
mes_max_ventas_año = ventas_por_año_mes.groupby("año").idxmax().apply(lambda x: x[1])

# 6. MES CON MENOS VENTAS PARA EL AÑO 2015 Y 2016 ---------------------------------------------------------------------------------------
# Mes con menores ventas para cada año
mes_min_ventas_año = ventas_por_año_mes.groupby("año").idxmin().apply(lambda x: x[1])

# 7. PORCENTAJE DE CRECIMIENTO EN VENTAS ANUAL ---------------------------------------------------------------------------------------
# Agrupar ventas por año 
ventas_año = BD.groupby(BD["Fecha"].dt.year)["Ventas Netas (USD)"]

# Calcular el cambio porcentual entre cada par de años consecutivos
crecimiento_ventas_anual = ventas_año.pct_change() * 100
#print(crecimiento_ventas_anual)
#print(crecimiento_ventas_anual.iloc[-1])

# 8. Rentabilidad septiembre 2016 ---------------------------------------------------------------------------------------
rentabilidad_por_año_mes = ((ventas_por_año_mes - costos_por_año_mes) / ventas_por_año_mes) * 100
#print(rentabilidad_por_año_mes)

#print("Rentabilidad mes de septimbre 2016", rentabilidad_por_año_mes[2016][9])
#print("Rentabilidad mes de septimbre 2015", rentabilidad_por_año_mes[2015][9])

# Convertir el índice multinivel en un DataFrame y resetear el índice
rentabilidad_por_año_mes_df = rentabilidad_por_año_mes.reset_index()

# Convertir las columnas 'año' y 'mes' en strings
rentabilidad_por_año_mes_df['año'] = rentabilidad_por_año_mes_df['año'].astype(str)
rentabilidad_por_año_mes_df['mes'] = rentabilidad_por_año_mes_df['mes'].astype(str)

# Agregar una columna 'Fecha' que concatene el año y el mes
rentabilidad_por_año_mes_df['Fecha'] = rentabilidad_por_año_mes_df['año'] + rentabilidad_por_año_mes_df['mes']

# Convertir la columna 'Fecha' a tipo datetime
rentabilidad_por_año_mes_df['Fecha'] = pd.to_datetime(rentabilidad_por_año_mes_df['Fecha'], format='%Y%m')

# Mostrar el DataFrame resultante
#print(rentabilidad_por_año_mes_df)

# 9. Trimestre con rentabilidad mas baja ---------------------------------------------------------------------------------------
# Rentabilidad por trimestre
ventas_por_trimestre = BD.groupby(["año", "Trimestre"])["Ventas Netas (USD)"].sum()
costos_por_trimestre = BD.groupby(["año", "Trimestre"])["Costo (USD)"].sum()
rentabilidad_por_trimestre = ventas_por_trimestre - costos_por_trimestre

# Identificar el trimestre menos rentable histórico
trimestre_menor_rentabilidad_historico = rentabilidad_por_trimestre.idxmin()

# Permitir la selección del trimestre más bajo por año
trimestre_menor_rentabilidad_por_año = rentabilidad_por_trimestre.groupby("año").idxmin()
#print(trimestre_menor_rentabilidad_historico)
#print(trimestre_menor_rentabilidad_por_año)
#print((str(trimestre_menor_rentabilidad_por_año[2015]).split('Q')[1])[0])

# 10. Cliente menos rentable y el año ---------------------------------------------------------------------------------------
ventas_por_cliente_año = BD.groupby(["Número de Cliente", "año"])["Ventas Netas (USD)"].sum()
costos_por_cliente_año = BD.groupby(["Número de Cliente", "año"])["Costo (USD)"].sum()
rentabilidad_clientes = ventas_por_cliente_año - costos_por_cliente_año
#print(rentabilidad_clientes[17])
cliente_menos_rentable_año = rentabilidad_clientes.idxmin()
#print(cliente_menos_rentable_año)
##------------------------------------------------------------------------------
## DATA VISUALIZATION ----------------------------------------------------------
##------------------------------------------------------------------------------
# Obtener valores unicos para el filtro por años
years = list(BD["Fecha"].dt.year.astype(str).unique())

text1 = ""
text2 = ""
text3 = ""
text4 = ""
text5 = ""
text6 = f"Cliente({cliente_menos_rentable_año[0]}) - {cliente_menos_rentable_año[1]}"
#print(text6)

# Datos organizados de la base de datos --------------------------------------------------------------------
data = ""

# Datos para la grafica %Rentabilidad --------------------------------------------------------------------
ventas_fecha = BD.groupby("Fecha")["Ventas Netas (USD)"].sum()
costos_fecha = BD.groupby("Fecha")["Costo (USD)"].sum()
#print(costos_fecha)

rentabilidad_fecha = ((ventas_fecha - costos_fecha) / ventas_fecha) * 100
#print(rentabilidad_fecha)


df_rentabilidad_fecha = rentabilidad_fecha.to_frame(name = "%Rentabilidad").reset_index(names=["Fecha"])
#print(df_rentabilidad_fecha)
data1 = df_rentabilidad_fecha

# Datos para la grafica de barras -----------------------------------------------------------------------------


data2 = ""

#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------- DEFINITION OF THE PAGE -------------------------------------------------------------------------------------------------
page = """
# 📊 Report Dashboard

<|{year}|selector|lov={years}|dropdown|>


<|layout|columns=1 1 1|columns[mobile]=1 1|

<|Mes (+) Ventas {year}:|text|>

<|%Crecimiento de Ventas:|text|>

<|Vendedor (+) Clientes {year}:|text|>

<|$USD {text1}|text|>

<|{text2}|text|>

<|{text3}|text|>

<|Mes (-) Ventas {year}:|text|>

<|Trimestre (+)BAJO:|text|>

<|Cliente (-) Rentable Historico:|text|>

<|$USD {text4}|text|>

<|Q {text5}|text|>

<|{text6}|text|>

|>

## Histórico Rentabilidad

<|{data1}|chart|mode=lines|x=Fecha|y[1]=%Rentabilidad|line[1]=dash|color[1]=red|>

## Analisis ParetoABC x Departamento

<|{data2}|chart|type=bar|x=Year|y[1]=GrupoA|y[2]=GrupoB|y[3]=GrupoC|color[1]=green|color[2]=blue|color[3]=red|>

"""

if __name__ == "__main__":
    # Define el año inicial
    year = None
    data = None
    
Gui(page).run(
    title="Report Dashboard",
    use_reloader=True,
    debug=True,
)