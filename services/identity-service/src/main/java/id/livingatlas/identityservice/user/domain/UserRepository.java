package id.livingatlas.identityservice.user.domain;

import id.livingatlas.identityservice.model.User;
import id.livingatlas.identityservice.model.UserStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {

    Optional<User> findByEmail(String email);

    Optional<User> findByUsername(String username);

    boolean existsByEmail(String email);

    boolean existsByUsername(String username);

    Page<User> findAllByStatus(UserStatus status, Pageable pageable);

    Page<User> findAllByCreatedAtAfter(OffsetDateTime since, Pageable pageable);
}