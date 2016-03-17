FROM docker.io/jboss/dogen:1.5.0

ADD template.jinja /opt/dogen/dogen/templates/template.jinja
ADD jboss.repo /opt/additional_scripts/
RUN pip install -U .

