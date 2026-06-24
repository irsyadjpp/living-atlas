package id.livingatlas.contentservice.source.infrastructure;

import id.livingatlas.contentservice.source.domain.Channel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface ChannelRepository extends JpaRepository<Channel, UUID> {
    Optional<Channel> findByPlatformAndPlatformChannelId(String platform, String platformChannelId);
}