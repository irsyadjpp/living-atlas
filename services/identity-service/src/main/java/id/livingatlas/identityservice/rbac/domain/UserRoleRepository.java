package id.livingatlas.identityservice.rbac.domain;

import id.livingatlas.identityservice.user.domain.model.UserRole;
import id.livingatlas.identityservice.user.domain.model.UserRoleId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface UserRoleRepository extends JpaRepository<UserRole, UserRoleId> {

    List<UserRole> findAllByUserId(UUID userId);

    List<UserRole> findAllByRoleId(UUID roleId);

    List<UserRole> findAllByTenantId(UUID tenantId);

    List<UserRole> findAllByUserIdAndTenantId(UUID userId, UUID tenantId);
}