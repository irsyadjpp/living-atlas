package id.livingatlas.researchservice.genome.domain;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.UUID;

@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class StorySimilarityId implements Serializable {
    private UUID storyIdA;
    private UUID storyIdB;
}