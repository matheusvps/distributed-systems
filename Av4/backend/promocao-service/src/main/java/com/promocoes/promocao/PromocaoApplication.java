package com.promocoes.promocao;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.promocoes")
public class PromocaoApplication {

    public static void main(String[] args) {
        SpringApplication.run(PromocaoApplication.class, args);
    }
}
