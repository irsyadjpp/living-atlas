package id.livingatlas.identityservice.rbac.domain.model;

import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Getter
@Setter
@ToString
@EqualsAndHashCode
@NoArgsConstructor
@Table(name = "permissions", schema = "iam")
public class Permission {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String code;

    @Column(name = "resource_type", nullable = false)
    private String resourceType;

    @Column(nullable = false)
    private String action;

    @Column(columnDefinition = "TEXT")
    private String description;

    public Permission(String code, String resourceType, String action) {
        this.code = code;
        this.resourceType = resourceType;
        this.action = action;
    }
}