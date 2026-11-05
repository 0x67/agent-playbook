#!/bin/sh
set -e
mkdir -p src/main/java/app
cat > pom.xml <<'X'
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>app</groupId>
  <artifactId>fetcher</artifactId>
  <version>1.0.0</version>
  <properties>
    <maven.compiler.release>25</maven.compiler.release>
  </properties>
</project>
X
cat > src/main/java/app/Fetcher.java <<'X'
package app;

import java.io.BufferedWriter;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;

public final class Fetcher {
    private final HttpClient client = HttpClient.newHttpClient();
    private final Map<String, Integer> sizes = new HashMap<>();
    private final Object auditLock = new Object();
    private final BufferedWriter audit;

    public Fetcher(BufferedWriter audit) {
        this.audit = audit;
    }

    /** Fetches every URL on its own virtual thread and returns body sizes by URL. */
    public Map<String, Integer> fetchAll(List<String> urls) {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (String url : urls) {
                executor.submit(() -> {
                    String body = get(url);
                    synchronized (auditLock) {
                        audit.write(url + " " + body.length() + "\n");
                    }
                    sizes.put(url, body.length());
                    return null;
                });
            }
        }
        return sizes;
    }

    private String get(String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder(URI.create(url)).build();
        return client.send(request, HttpResponse.BodyHandlers.ofString()).body();
    }
}
X
