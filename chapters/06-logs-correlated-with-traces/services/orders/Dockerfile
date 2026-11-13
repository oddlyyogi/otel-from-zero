FROM eclipse-temurin:25-jre
WORKDIR /app
COPY opentelemetry-javaagent.jar .
COPY target/orders-1.0.0.jar app.jar
ENV JAVA_TOOL_OPTIONS="-javaagent:/app/opentelemetry-javaagent.jar"
CMD ["java", "-jar", "app.jar"]