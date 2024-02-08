import streamlit as st
import posixpath
import pandas as pd
from urllib.parse import unquote, urlparse
from pathlib import PosixPath, PurePosixPath
import logging
logging.basicConfig(filename='test.log')


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

#Obtiene el número de veces que se repite cada anchor.
#Devuelve un DataFrame con las columnas "Anchor" y "Num. veces"
def getAnchors(df_enlaces): 
    conteo_elementos = df_enlaces['Anchor'].value_counts().to_frame("Num. veces")
    conteo_elementos.reset_index(inplace=True)
    df_anchors=conteo_elementos.rename(columns={'index':'Anchors'})
    if df_anchors is not None:
        df_anchors=df_anchors.sort_values("Num. veces",ascending=False)
    return df_anchors

#Obtiene el número de veces que se repite cada anchor en cada destino
#Devuelve un DataFrame con las columnas "Anchor", "URL destino" y "Num. veces"
def getDataframeAnchorsDestino(df_enlaces):
    #Contamos las repeticiones de elementos: Anchor, Destination. Lo devuelve en formato serie.
    serie = df_enlaces.pivot_table(index = ['Anchor',"Destination"], aggfunc ='size')
    df_final=serie.to_frame("Num. veces")
    df_final.reset_index(inplace=True)
    if df_final is not None:
        df_final=df_final.sort_values("Num. veces",ascending=False)
    return df_final

###Para pasar la pivot table dinámica con los datos de repeticiones de anchors a DataFrame
#COmo índice tiene la tupla anchor, URL destino y como valor el número de repeticiones
def serieTuplaValor2DataFrame(serie):
    df=pd.DataFrame(columns=['Anchor', 'URL destino', 'Num. veces'])
    for indice, valor in serie.iteritems():
        nueva_fila=pd.Series({'Anchor':indice[0],'URL destino':indice [1],'Num. veces':valor})
        df = pd.concat([df, nueva_fila.to_frame().T], ignore_index=True)
    return df

st.set_page_config(
   page_title="Arquitectura y contenidos"
)
st.title("Arquitectura y contenidos")
st.text("Devuelve datos relativos a la arquitectura y los contenidos.")
st.text("Tenemos únicamente en cuenta contenidos indexables")



f_entrada=st.file_uploader('CSV con datos exportados de Screaming Frog (internal_all.csv)', type='csv')

content_type='html'
indexables='Indexable'

if f_entrada is not None:
    df=pd.read_csv(f_entrada)

    #Filtramos los resultados html e indexables
    df_mask=(df['Content Type'].str.contains(content_type))&(df['Indexability']==indexables)
    df_html=df[df_mask]

    #Mostramos las URL más enlazadas
    df_top_enlaces=df_html[['Address','Unique Inlinks', 'Inlinks', 'Crawl Depth']].sort_values(by='Unique Inlinks',ascending=False).reset_index(drop=True)
    st.subheader('Top de URL enlazadas')
    st.dataframe(df_top_enlaces, width=1000)
    st.download_button(
        label="Descargar como CSV",
        data=df_top_enlaces.to_csv(index = False).encode('utf-8'),
        file_name='top_enlazadas.csv',
        mime='text/csv',
    )

    
    #Obtenemos la ruta de directorios hasta el nivel especificado
    niveles_directorios=st.number_input(min_value=1,max_value=6,value=2,label='Seleccione el nivel de directorios a obtener')
    i=1
    while i <= niveles_directorios:
        df_html['Directorio_'+str(i)]=df_html['Address'].apply(lambda x:getPathUrl(x,i))
        i+=1
    
    n_dir='Directorio_'+str(niveles_directorios)
    lista_directorios=df_html[n_dir].unique().tolist()
    #Eliminamos el que venga vacío, porque realmente no existe
    directorios = list(filter(None, lista_directorios))

    df_dir=pd.DataFrame(columns=[n_dir, 'Num Pages', 'Unique Inlinks', 'Unique Outlinks'])
    df_dir[n_dir]=directorios

    #Calculamos el número de páginas, inlinks y outlinks por directorio
    for i in range(len(df_dir)):
        dir_actual=df_dir.loc[i,n_dir]
        df_temporal=df_html[df_html[n_dir]==dir_actual]
        df_dir.loc[i,"Num Pages"]=len(df_temporal.index)
        df_dir.loc[i,'Unique Inlinks']=df_temporal['Unique Inlinks'].sum()
        df_dir.loc[i,'Unique Outlinks']=df_temporal['Unique Outlinks'].sum()    
        df_dir.loc[i,'Media de palabras']=df_temporal['Word Count'].mean().round() 
        df_dir.loc[i,'Mediana de palabras']=df_temporal['Word Count'].median().round() 
       

    st.subheader('Análisis por directorio')
    st.dataframe(df_dir, width=1000)
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
    dominio=st.text_input("Dominio (para extraer únicamente enlaces internos)")
    f_enlaces=st.file_uploader('CSV con export de Inlinks Screaming Frog (all_inlinks.csv)', type='csv')
    if f_enlaces is not None:
        #Columnas sonbre las que vamos a trabajar
        columnas=["Type","Source","Destination","Alt Text","Anchor","Status Code"]
        df_enlaces=pd.read_csv(f_enlaces, usecols=columnas)
        #Filtramos solo enlaces en hyperlinks e imágenes
        df_hyperlinks=df_enlaces[df_enlaces['Type'].isin(['Hyperlink','Image'])]
        #Dejamos sólo elaces a URL internas dentro del dominio enlazado
        df_internal_links=df_hyperlinks[df_hyperlinks['Destination'].str.contains(dominio,na=False)]
        #Hacemos una copia para que no de problemas al trabajar e intentar rellenar los campos vacíos
        df_copy=df_internal_links.copy()
        #Si Anchor es vacío incluimos el valor del atributo alt
        df_copy['Anchor'].fillna(df_internal_links['Alt Text'], inplace=True)
        #Contamos las repeticiones de elementos: Anchor
        df_anchors=getAnchors(df_copy)

        st.subheader("Todos los anchors")
        st.dataframe(df_anchors, width=1000)
        st.download_button(
            label="Descargar como CSV",
            data=df_anchors.to_csv(index = None, quotechar='"').encode('utf-8'),
            file_name='anchors.csv',
            mime='text/csv',
        )

        #Contamos las repeticiones de elementos: Anchor, Destination. 
        df_anchors_dest=getDataframeAnchorsDestino(df_copy)

        st.subheader("Anchors por destino")
        st.dataframe(df_anchors_dest, width=1000)
        st.download_button(
            label="Descargar como CSV",
            data=df_anchors_dest.to_csv(index = None, quotechar='"').encode('utf-8'),
            file_name='anchors_dest.csv',
            mime='text/csv',
        )