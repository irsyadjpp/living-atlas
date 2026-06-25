package id.livingatlas.identityservice.preferences.infrastructure;

import id.livingatlas.identityservice.preferences.domain.UserPreference;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface UserPreferenceRepository extends JpaRepository<UserPreference, UUID> {
    Optional<UserPreference> findByUserIdAndPreferenceKey(UUID userId, String preferenceKey);
    java.util.List<UserPreference> findByUserId(UUID userId);
}