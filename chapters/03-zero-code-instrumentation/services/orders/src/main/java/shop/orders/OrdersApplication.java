package shop.orders;

import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

@SpringBootApplication
@RestController
public class OrdersApplication {
    private final RestClient inventory;

    OrdersApplication(@Value("${inventory.url}") String inventoryUrl) {
        this.inventory = RestClient.create(inventoryUrl);
    }

    public static void main(String[] args) {
        SpringApplication.run(OrdersApplication.class, args);
    }

    @PostMapping("/orders")
    public Map<?, ?> place(@RequestBody Map<String, Object> order) {
        return inventory.post().uri("/reserve").body(order).retrieve().body(Map.class);
    }
}