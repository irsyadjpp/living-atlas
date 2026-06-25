package id.livingatlas.identityservice.user.domain.model;

import jakarta.persistence.Embeddable;
import lombok.*;

import java.io.Serializable;
import java.util.UUID;

@Embeddable
@Getter
@Setter
@ToString
@EqualsAndHashCode
@NoArgsConstructor
@AllArgsConstructor
public class UserRoleId implements Serializable {

    private UUID userId;

    private UUID roleId;

    private UUID tenantId;

    private UUID workspaceId;
}