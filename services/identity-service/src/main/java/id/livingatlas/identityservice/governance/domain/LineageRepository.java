package id.livingatlas.identityservice.governance.domain;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface LineageRepository extends JpaRepository<Lineage, UUID> {

    List<Lineage> findAllByTargetTypeAndTargetId(String targetType, UUID targetId);

    List<Lineage> findAllBySourceTypeAndSourceId(String sourceType, UUID sourceId);
}