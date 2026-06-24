package id.livingatlas.knowledgeservice.motifs.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "motifs", schema = "knowledge")
@Getter
@Setter
@NoArgsConstructor
public class Motif {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(unique = true, length = 255)
    private String slug;

    @Column(nullable = false, columnDefinition = "text")
    private String name;

    @Column(columnDefinition = "text")
    private String description;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;
}