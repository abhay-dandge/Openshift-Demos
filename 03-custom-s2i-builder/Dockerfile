# Official Red Hat UBI 9 Minimal Custom S2I Builder Image
FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

# Metadata labels required by the OpenShift S2I specification
LABEL maintainer="Red Hat OpenShift Community" \
      io.k8s.description="Custom S2I Builder Image for Static Web & Lightweight Python Microservices" \
      io.k8s.display-name="Custom UBI9 S2I Web Builder" \
      io.openshift.expose-services="8080:http" \
      io.openshift.tags="builder,s2i,ubi9,web,python" \
      io.openshift.s2i.scripts-url="image:///usr/libexec/s2i"

ENV APP_ROOT=/opt/app-root \
    PATH=/opt/app-root/src/bin:/opt/app-root/bin:$PATH \
    PORT=8080 \
    HOME=/opt/app-root

# Install runtime dependencies (Python 3 and tar for S2I artifacts)
RUN microdnf --nodocs -y install python3 python3-pip tar shadow-utils && \
    microdnf clean all && \
    rm -rf /var/cache/yum

# Create directory structure compliant with OpenShift arbitrary UID guidelines
# UID 1001 is standard non-privileged user, Group 0 (root group) permissions are mandatory
RUN mkdir -p ${APP_ROOT}/src ${APP_ROOT}/bin /usr/libexec/s2i && \
    useradd -u 1001 -r -g 0 -d ${APP_ROOT} -s /sbin/nologin -c "Default Application User" default

# Copy S2I lifecycle scripts into designated image location
COPY .s2i/bin/ /usr/libexec/s2i/

# Crucial OpenShift permission fix: Group 0 must have write access for arbitrary UIDs
RUN chown -R 1001:0 ${APP_ROOT} /usr/libexec/s2i && \
    chmod -R g=u ${APP_ROOT} /usr/libexec/s2i && \
    chmod +x /usr/libexec/s2i/*

WORKDIR ${APP_ROOT}/src

# Set default non-root user (OpenShift will override UID at runtime, but GID stays 0)
USER 1001

EXPOSE 8080

CMD ["/usr/libexec/s2i/usage"]
