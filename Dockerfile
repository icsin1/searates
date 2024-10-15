FROM node:18-alpine3.17 AS node

WORKDIR /

#Custom addons copy for node
COPY addons/base_document_reports_stimulsoft ./base_document_reports_stimulsoft

WORKDIR /base_document_reports_stimulsoft/static/src/libs/stimulsoft-nodejs
RUN npm install

# Use the SearatesERP Saas Kit docker images
FROM searateserpacr.azurecr.io/searatesrepo:serp-saas-15.0

# Author details
LABEL org.opencontainers.image.authors="SearatesERP Framework Team <framework-team@searateserp.com>"

# Copy the dependences
COPY requirements.txt /tmp/serp-requirements.txt
RUN /opt/bitnami/odoo/venv/bin/pip3 install -r /tmp/serp-requirements.txt

#Copy Deafult Odoo Conf File
COPY odoo.conf.tpl /opt/bitnami/scripts/odoo/bitnami-templates/odoo.conf.tpl

#Custom addons
COPY addons /opt/bitnami/odoo/addons

# Copying Node library to repository
COPY --from=node /base_document_reports_stimulsoft/static/src/libs/stimulsoft-nodejs /opt/bitnami/odoo/addons/base_document_reports_stimulsoft/static/src/libs/stimulsoft-nodejs

USER root

RUN mkdir -p /home/odoo
RUN chown -R odoo:odoo /home/odoo/
RUN chmod -R 777 /home/odoo/
RUN if [ -d "/.cache" ]; then chmod -R 777 /.cache; fi
