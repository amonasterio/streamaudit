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
st.text("Devuelve datos relativos a la arquitectura y los contenidos.")
st.text("Tenemos únicamente en cuenta contenidos indexables")

niveles_directorios=st.number_input(min_value=1,max_value=5,value=2,label='Seleccione el nivel de directorios a obtener')

f_entrada=st.file_uploader('CSV con datos exportados de Screaming Frog (internal_all.csv)', type='csv')

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

    df_top_enlaces=df_html[['Address','Unique Inlinks', 'Inlinks']].sort_values(by='Unique Inlinks',ascending=False).reset_index(drop=True)
    st.subheader('Top de URL enlazadas')

    st.dataframe(df_top_enlaces, height=500, width=1000)
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
    

    st.subheader('Densidad de contenido')
    max_word_count=df_html["Word Count"].max()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Max. palabras en URL", value=max_word_count)
    with col2:
        st.metric(label="Min. palabras en URL", value=df_html["Word Count"].min())
    with col3:
        st.metric(label="Media palabras en URL", value=int(df_html["Word Count"].mean()))
    with col4:
        st.metric(label="Mediana palabras en URL", value=int(df_html["Word Count"].median()))
    
    inferior=st.number_input(min_value=0,max_value=max_word_count,value=400,label='Seleccione valor intermedio inferior')
    superior=st.number_input(min_value=inferior,max_value=max_word_count,value=int((inferior+max_word_count)/2),label='Seleccione valor intermedio superior')
    limites=[inferior,superior]
    str_bajo='Bajo [0,'+str(limites[0])+']'
    str_medio='Medio ['+str(limites[0])+'-'+str(limites[1])+']'
    str_alto='Alto ['+str(limites[1])+'-...]'


    dict_contenido={
        str_bajo:len(df_html[df_html["Word Count"]<=limites[0]].index),
        str_medio:len(df_html[(df_html["Word Count"]>limites[0]) &(df_html["Word Count"]<=limites[1])].index),
        str_alto:len(df_html[df_html["Word Count"]>limites[1]].index)
    }
    
    st.dataframe(pd.DataFrame(dict_contenido,index=[0]))

    st.subheader('Anchor text utilizados')
    f_enlaces=st.file_uploader('CSV con export de Inlinks Screaming Frog (all_inlinks.csv)', type='csv')
    if f_enlaces is not None:
        df_enlaces=pd.read_csv(f_enlaces)
        df_hiperlinks=df_enlaces[df_enlaces['Type']=='Hyperlink']

        lista_anchors=df_hiperlinks['Anchor'].unique().tolist()


        df_anchors=pd.DataFrame(columns=['Anchor', 'Num. veces'])
        df_anchors['Anchor']=lista_anchors
        for i in range(len(df_anchors)):
            anchor_actual=df_anchors.loc[i,'Anchor']
            df_temporal=df_enlaces[df_enlaces['Anchor']==anchor_actual]
            df_anchors.iloc[i,1]=len(df_temporal.index)
            df_anchors=df_anchors.sort_values(by='Num. veces',ascending=False).reset_index(drop=True)
        st.dataframe(df_anchors, width=500)
        st.download_button(
            label="Descargar como CSV",
            data=df_dir.to_csv(index = False).encode('utf-8'),
            file_name='anchors.csv',
            mime='text/csv',
        )