FROM docker.io/jboss/dogen:1.4.0

ADD template.jinja /opt/dogen/dogen/templates/template.jinja
ADD jboss.repo /opt/additional_scripts/
RUN sed -i "s|\"\(.*\)\"|\"\1-redhat\"|" dogen/version.py
RUN pip install -U .

