FROM docker.io/jboss/dogen:1.3.0

ADD template.jinja /opt/dogen/dogen/templates/template.jinja
RUN pip install -U .

