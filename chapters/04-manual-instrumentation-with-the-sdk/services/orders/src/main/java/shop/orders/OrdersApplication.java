package shop.orders;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.baggage.Baggage;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestClient;

@SpringBootApplication
@RestController
public class OrdersApplication {
    private final RestClient inventory;
    private static final Map<String, Double> PRICES =
            Map.of("mug", 12.0, "tee", 20.0, "cap", 15.0);
    private final Tracer tracer = GlobalOpenTelemetry.getTracer("orders", "1.0.0");

    OrdersApplication(@Value("${inventory.url}") String inventoryUrl) {
        this.inventory = RestClient.create(inventoryUrl);
    }

    public static void main(String[] args) {
        SpringApplication.run(OrdersApplication.class, args);
    }

    @PostMapping("/orders")
    public ResponseEntity<Map<?, ?>> place(@RequestBody Map<String, Object> order) {
        String id = UUID.randomUUID().toString().substring(0, 8);
        Span span = Span.current();
        span.setAttribute("shop.order.id", id);
        try {
            Map<?, ?> reserved = reserve((String) order.get("sku"), order);
            span.addEvent("order placed");
            int qty = ((Number) order.get("qty")).intValue();
            double total = price((String) order.get("sku"), qty);
            return ResponseEntity.ok(Map.of("order", id, "total", total, "reserved", reserved));
        } catch (HttpClientErrorException.Conflict e) {
            span.recordException(e);
            span.setStatus(StatusCode.ERROR, "out of stock");
            return ResponseEntity.status(409)
                    .body(Map.of("order", id, "error", "out of stock"));
        }
    }

    double price(String sku, int qty) {
        Span span = tracer.spanBuilder("price order").startSpan();
        try (Scope scope = span.makeCurrent()) {
            String tier = Baggage.current().getEntryValue("shop.customer.tier");
            double total = PRICES.getOrDefault(sku, 0.0) * qty;
            if ("gold".equals(tier)) total = total * 0.9;
            span.setAttribute("shop.customer.tier", String.valueOf(tier));
            span.setAttribute("shop.order.total", total);
            return total;
        } finally {
            span.end();
        }
    }

    @WithSpan("reserve stock")
    Map<?, ?> reserve(@SpanAttribute("shop.sku") String sku, Map<String, Object> order) {
        return inventory.post().uri("/reserve").body(order).retrieve().body(Map.class);
    }
}