import streamlit as st
import posixpath
import pandas as pd
from urllib.parse import unquote, urlparse
from pathlib import PosixPath, PurePosixPath

#Obtener los directorios de una URL por nivel
def getPathUrl(url, nivel):
    ruta=''
    paths = urlparse(url).path
    partes=PurePosixPath(unquote(paths)).parts
    if nivel < len(partes):
        i=1
        while i <= nivel:
            ruta+='/'+partes[i]
            i+=1
    return ruta

st.set_page_config(
   page_title="Arquitectura y contenidos"
)
st.title("Arquitectura y contenidos")
st.text("Devuelve datos relativos a la arquitectura y los contenidos")

niveles_directorios=st.number_input(min_value=1,max_value=5,value=2,label='Seleccione el nivel de directorios a obtener')

f_entrada=st.file_uploader('CSV con datos exportados de Screaming Frog', type='csv')

content_type='html'
indexables='Indexable'

if f_entrada is not None:
    df=pd.read_csv(f_entrada)
    #Obtenemos la ruta de directorios hasta el nivel especificado
    i=1
    while i <= niveles_directorios:
        df['Directorio_'+str(i)]=df['Address'].apply(lambda x:getPathUrl(x,i))
        i+=1
    #Filtramos los resultados html e indexables
    df_mask=(df['Content Type'].str.contains(content_type))&(df['Indexability']==indexables)
    df_html=df[df_mask]
    n_dir='Directorio_'+str(niveles_directorios)
    lista_directorios=df_html[n_dir].unique().tolist()
    #Eliminamos el que venga vacío, porque realmente no existe
    directorios = list(filter(None, lista_directorios))

    df_dir=pd.DataFrame(columns=[n_dir, 'Num Pages', 'Unique Inlinks', 'Unique Outlinks'])
    df_dir[n_dir]=directorios

    df_top_enlaces=df_html[['Address','Unique Inlinks', 'Inlinks']].sort_values(by='Unique Inlinks',ascending=False)
    st.subheader('Top de URL enlazadas')
    st.dataframe(df_top_enlaces, height=500, width=500)
    st.download_button(
                label="Descargar como CSV",
                data=df_dir.to_csv(index = False).encode('utf-8'),
                file_name='top_enlazadas.csv',
                mime='text/csv',
            )

    #Calculamos el número de páginas, inlinks y outlinks por directorio
    for i in range(len(df_dir)):
        dir_actual=df_dir.loc[i,n_dir]
        df_temporal=df_html[df_html[n_dir]==dir_actual]
        df_dir.loc[i,"Num Pages"]=len(df_temporal.index)
        df_dir.loc[i,'Unique Inlinks']=df_temporal['Unique Inlinks'].sum()
        df_dir.loc[i,'Unique Outlinks']=df_temporal['Unique Outlinks'].sum()
    
    st.subheader('Análisis por directorio')
    st.dataframe(df_dir, height=500)
    st.download_button(
                label="Descargar como CSV",
                data=df_dir.to_csv(index = False).encode('utf-8'),
                file_name='directorios.csv',
                mime='text/csv',
            )

    limites=[450,1200]
    str_bajo='Bajo [0,'+str(limites[0])+']'
    str_medio='Medio ['+str(limites[0])+'-'+str(limites[1])+']'
    str_alto='Alto ['+str(limites[1])+'-...]'


    dict_contenido={
        str_bajo:len(df_html[df_html["Word Count"]<=limites[0]].index),
        str_medio:len(df_html[(df_html["Word Count"]>limites[0]) &(df_html["Word Count"]<=limites[1])].index),
        str_alto:len(df_html[df_html["Word Count"]>limites[1]].index)
    }
    st.subheader('Densidad de contenido')
    st.dataframe(pd.DataFrame(dict_contenido,index=[0]))

