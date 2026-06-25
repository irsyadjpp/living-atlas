package id.livingatlas.identityservice.rbac.domain;

import id.livingatlas.identityservice.rbac.domain.model.RolePermission;
import id.livingatlas.identityservice.rbac.domain.model.RolePermissionId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface RolePermissionRepository extends JpaRepository<RolePermission, RolePermissionId> {

    List<RolePermission> findAllByRoleId(UUID roleId);
}