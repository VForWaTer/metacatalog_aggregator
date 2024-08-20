# Pull any base image that includes python3
FROM python:3.12.2

# install the toolbox runner tools
RUN pip install "json2args>=0.6.2" \
    metacatalog==0.9.2 \    
    ipython==8.26.0 \ 
    pandas==2.2.2 \
    geopandas==1.0.1 \
    xarray[complete]==2024.7.0 \ 
    rioxarray==0.17.0 \
    polars-lts-cpu==1.1.0 \
    geocube==0.6.0

# create the tool input structure
RUN mkdir /in
COPY ./in /in
RUN mkdir /out
RUN mkdir /src
COPY ./src /src

# copy the citation file - looks funny to make COPY not fail if the file is not there
COPY ./CITATION.cf[f] /src/CITATION.cff

WORKDIR /src
CMD ["python", "run.py"]
