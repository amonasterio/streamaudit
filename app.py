import streamlit as st
import pandas as pd
from urllib.parse import unquote, urlparse
from pathlib import PurePosixPath
import logging
import matplotlib.pyplot as plt
logging.basicConfig(filename='test.log')

CANONICALISED='Canonicalised'
NO_RESPONSE="No Response"
BLOQUEADO_ROBOTS="Blocked by robots.txt"
NOINDEX="noindex"

#Definimos las columnas sobre las que trabajaremos y su tipo
columnas=["Address","Content Type","Status Code","Indexability","Indexability Status","Crawl Depth",'Unique Inlinks', 'Inlinks','Unique Outlinks', 'Outlinks','Word Count']
tipo={"Address": "string", "Content Type": "string", "Status Code":"int","Indexability":"string", "Indexability Status":"string","Crawl Depth":int,'Unique Inlinks':int, 'Inlinks':int,'Unique Outlinks':int, 'Outlinks':int,'Word Count':int}

def darFormatoPorcentaje(value_in):
    porcentaje = "{:.2%}".format(value_in)
    return porcentaje

#obtener el dominio de una URL
def getDomainFromUrl(url_in):
    # Parsear la URL
    parsed_url = urlparse(url_in)
    # Extraer el dominio
    dominio = parsed_url.netloc
    return dominio

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

#Genera un gráfico de tarta
def getPieChart(valores, etiquetas):
    fig, ax = plt.subplots() 
    ax.scatter(etiquetas, valores)
    # Create a pie chart
    plt.pie(valores, labels=etiquetas, autopct='%1.1f%%')
    return fig

#Filtra las URL en formato html o pdf validas en función de si son indexables, parcialmente indexables o todas
#NO USADO. ELIMINAR SI NO LO HACEMOS EN EL FUTURO
def filtraURLvalidas(df_in,tipo,formato_url):
    if formato_url=="Sólo HTML":
        content_type='html'
    else:
        content_type='pdf|html'
    if tipo=="Indexables":
        df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))&(df_in["Status Code"]==200)&(df_in['Indexability Status'].isna())
    elif tipo=="Potencialmente indexables":
        df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))&(df_in["Status Code"]==200)&((df_in['Indexability Status'].isna())|(df_in['Indexability Status']).eq(CANONICALISED))
    elif tipo=="Todas 200":
        df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))&(df_in["Status Code"]==200)
    elif tipo=="Todas":
         df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))
    df_out=df_in[df_mask]
    return df_out

#Filtra las URL en el formato indicado en función de si son indexables, parcialmente indexables o todas
def filtraURLFormatoTipo(df_in,dict_formato_url,tipo):
    content_type=''
    if dict_formato_url['html']:
        content_type='html'
    if dict_formato_url['pdf']:
        if len(content_type)>0:
            content_type+="|pdf"
        else:
            content_type='pdf'
    if dict_formato_url['imagen']:
        if len(content_type)>0:
            content_type+="|image"
        else:
            content_type='image'
    if tipo=="Indexables":
        df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))&(df_in["Status Code"]==200)&(df_in['Indexability Status'].isna())
    elif tipo=="Potencialmente indexables":
        df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))&(df_in["Status Code"]==200)&((df_in['Indexability Status'].isna())|(df_in['Indexability Status']).eq(CANONICALISED))
    elif tipo=="Todas 200":
        df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))&(df_in["Status Code"]==200)
    elif tipo=="Todas":
         df_mask=(df_in['Content Type'].str.contains(content_type,regex=True))
    df_out=df_in[df_mask]
    return df_out

#Validamos que hemos seleccionado al menos un formato
def validaCheckboxFormato(dict_formatos):
    enc=False
    indice = 0
    valores= list(dict_formatos.values())
    # Itera mientras el contador esté dentro del rango de claves
    while (not enc) & (indice < len(valores)) :
        valor = valores[indice]
        if valor:
            enc=True
        indice += 1
    return enc

#Excluir de un dataframe URL cuyo content type incuya image
def excluyeImagenes(df_in):
    df_mask=~df_in['Content Type'].str.contains('image',regex=True)
    df_filtrado = df_in[df_mask]
    return df_filtrado

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



f_entrada=st.file_uploader('CSV con datos exportados de Screaming Frog (internal_all.csv)', type='csv')

content_type='html'
indexables='Indexable'

if f_entrada is not None:
    df_entrada=pd.read_csv(f_entrada,usecols=columnas, dtype=tipo)
    st.subheader('Resumen del crawl')
    #Obtenemos un resumen de las URL rastreadas
    u_total=len(df_entrada.index)
    u_indexables=(df_entrada['Indexability']=='Indexable').sum()
    u_canonicalizadas=(df_entrada['Indexability Status']==CANONICALISED).sum()
    u_noindex=(df_entrada['Indexability Status']==NOINDEX).sum()
    u_30X=((df_entrada['Status Code']>=300)&(df_entrada['Status Code']<400)).sum()
    u_40X=((df_entrada['Status Code']>=400)&(df_entrada['Status Code']<500)).sum()
    u_50X=((df_entrada['Status Code']>=500)&(df_entrada['Status Code']<600)).sum()
    u_noresponse=(df_entrada['Indexability Status']==NO_RESPONSE).sum()
    u_bloqueado=(df_entrada['Indexability Status']==BLOQUEADO_ROBOTS).sum()
    valores={"Indexables":[u_indexables], "Canonicalizadas":[u_canonicalizadas], "Noindex":[u_noindex], "Redirección 30X":[u_30X],"Error 40X":[u_40X], "Error 50X":[u_50X], "No Response":[u_noresponse], "Bloqueadas por robots":[u_bloqueado]}
    df_resumen=pd.DataFrame(valores)
    df_traspuesta = df_resumen.T.rename(columns={0: 'Número de URL'})
    df_traspuesta["Porcentaje"]=df_traspuesta.iloc[:, 0]/u_total
    fig=getPieChart(df_traspuesta['Número de URL'].tolist(), list(df_traspuesta.index))
    st.pyplot(fig)


    st.dataframe(df_traspuesta, width=1000)
    st.download_button(
        label="Descargar como CSV",
        data=df_traspuesta.to_csv().encode('utf-8'),
        file_name='resumen.csv',
        mime='text/csv',
    )

    st.subheader('Seleccionamos los tipos de URL sobre los que trabajaremos')
    st.write("Tipos de URL que tendremos en cuenta. Para que cuenta las palabras de los PDF en el crawl debemos habilitar: Spider > Extraction > Store PDF")
    c_html=st.checkbox('HTML',value=True)
    c_pdf=st.checkbox('PDF')
    c_img=st.checkbox('Imagen')
    d_formato={'html':c_html,"pdf":c_pdf,'imagen':c_img}

    tipo_resultados= st.radio(
     "Tipo de URL que tendremos en cuenta",
     ['Indexables', 'Potencialmente indexables', 'Todas 200','Todas'], help='***Indexables***=URL 200, sin noindex y sin canonicalizar\n\n***Potencialmente indexables***=URL 200, sin noindex'+
     '\n\n***Todas 200***=Todas las URL que devuelven 200\n\n***Todas***=Todas las URL rastreadas')

    if not validaCheckboxFormato(d_formato):
        st.warning("Debe seleccionar al menos un formato")
    else:

        #Filtramos los resultados en función de la opción escogida
        df_filtrado=filtraURLFormatoTipo(df_entrada,d_formato,tipo_resultados)

        #Mostramos las URL más enlazadas
        df_top_enlaces=df_filtrado[['Address', "Status Code", 'Indexability', 'Indexability Status','Unique Inlinks', 'Inlinks', 'Crawl Depth']].sort_values(by='Unique Inlinks',ascending=False).reset_index(drop=True)
        st.subheader('Top de URL enlazadas')
        st.dataframe(df_top_enlaces, width=1000)
        st.download_button(
            label="Descargar como CSV",
            data=df_top_enlaces.to_csv(index = False).encode('utf-8'),
            file_name='top_enlazadas.csv',
            mime='text/csv',
        )

        st.text(df_filtrado.shape[0])
        #Obtenemos la ruta de directorios hasta el nivel especificado
        niveles_directorios=st.number_input(min_value=1,max_value=6,value=2,label='Seleccione el nivel de directorios a obtener')
        i=1
        while i <= niveles_directorios:
            df_filtrado['Directorio_'+str(i)]=df_filtrado['Address'].apply(lambda x:getPathUrl(x,i))
            i+=1
        
        n_dir='Directorio_'+str(niveles_directorios)
        lista_directorios=df_filtrado[n_dir].unique().tolist()
        #Eliminamos el que venga vacío, porque realmente no existe
        directorios = list(filter(None, lista_directorios))

        df_dir=pd.DataFrame(columns=[n_dir, 'Num Pages', 'Unique Inlinks', 'Unique Outlinks'])
        df_dir[n_dir]=directorios

        
        #Calculamos el número de páginas, inlinks y outlinks por directorio
        for i in range(len(df_dir)):
            dir_actual=df_dir.loc[i,n_dir]
            df_temporal=df_filtrado[df_filtrado[n_dir]==dir_actual]
            df_dir.loc[i,"Num Pages"]=len(df_temporal.index)
            df_dir.loc[i,"Indexables"]=(df_temporal['Indexability']=='Indexable').sum()
            df_dir.loc[i,"No Indexables"]=(df_temporal['Indexability']=='Non-Indexable').sum()
            df_dir.loc[i,"Canonicalizadas"]=(df_temporal['Indexability Status']==CANONICALISED).sum()
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
        #Para calcular la densidad de contenido sacamos las imágenes ya que su contenido será 0 y afectará a la media y la mediana
        df_sin_imagenes=excluyeImagenes(df_filtrado)
        max_word_count=df_sin_imagenes["Word Count"].max()
        #Si hay contenido en las URL. Puede que no lo haya si sólo hemos seleccionado imágenes
        if max_word_count>0:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(label="Max. palabras en URL", value=max_word_count)
            with col2:
                st.metric(label="Min. palabras en URL", value=df_sin_imagenes["Word Count"].min())
            with col3:
                st.metric(label="Media palabras en URL", value=int(df_sin_imagenes["Word Count"].mean()))
            with col4:
                st.metric(label="Mediana palabras en URL", value=int(df_sin_imagenes["Word Count"].median()))
            
            inferior_defecto=400
            #Si la URL que más palabras tiene es inferior a 400. Modificamos el valor pod detecto
            if max_word_count<400:
                inferior_defecto=int(max_word_count/3)
            inferior=st.number_input(min_value=0,max_value=max_word_count,value=inferior_defecto,label='Seleccione valor intermedio inferior')
            superior=st.number_input(min_value=inferior,max_value=max_word_count,value=int((inferior+max_word_count)/2),label='Seleccione valor intermedio superior')
            limites=[inferior,superior]
            str_bajo='Bajo [0,'+str(limites[0])+']'
            str_medio='Medio ['+str(limites[0])+'-'+str(limites[1])+']'
            str_alto='Alto ['+str(limites[1])+'-...]'


            dict_contenido={
                str_bajo:len(df_sin_imagenes[df_sin_imagenes["Word Count"]<=limites[0]].index),
                str_medio:len(df_sin_imagenes[(df_sin_imagenes["Word Count"]>limites[0]) &(df_sin_imagenes["Word Count"]<=limites[1])].index),
                str_alto:len(df_sin_imagenes[df_sin_imagenes["Word Count"]>limites[1]].index)
            }
            
            st.dataframe(pd.DataFrame(dict_contenido,index=[0]))
        else:
            st.write("No se ha detectado contenido")

        st.subheader('Anchor text utilizados')
        #Obtnemos el dominio sobre el que queremos analizar los enlaces entrantes
        primer_elemento = df_top_enlaces.iloc[0]['Address']
        dominio=getDomainFromUrl(primer_elemento)
        dominio_input=st.text_input("Dominio (para extraer únicamente enlaces internos)",dominio)
        f_enlaces=st.file_uploader('CSV con export de Inlinks Screaming Frog (all_inlinks.csv)', type='csv')
        if f_enlaces is not None:
            #Columnas sonbre las que vamos a trabajar
            columnas_enlaces=["Type","Source","Destination","Alt Text","Anchor","Status Code"]
            tipo_columnas_enlaces={"Type":"string", "Source":"string", "Destination":"string","Alt Text":"string","Anchor":"string","Status Code":int}
            df_enlaces=pd.read_csv(f_enlaces, usecols=columnas_enlaces,dtype=tipo_columnas_enlaces)
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