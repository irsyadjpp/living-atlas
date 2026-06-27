package id.livingatlas.knowledgeservice.beliefs.application;

import id.livingatlas.knowledgeservice.beliefs.domain.Belief;
import id.livingatlas.knowledgeservice.beliefs.infrastructure.BeliefRepository;
import id.livingatlas.sharedweb.exception.ApiException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class BeliefService {

    private final BeliefRepository beliefRepository;

    @Transactional
    public Belief createBelief(Belief belief) {
//        belief.setStatus("active");
        Belief saved = beliefRepository.save(belief);
        log.info("Belief created: id={}, name={}", saved.getId(), saved.getName());
        return saved;
    }

    @Transactional(readOnly = true)
    public Belief getBelief(UUID id) {
        return beliefRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Belief not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Belief> listBeliefs(int page, int size) {
        return beliefRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Belief updateBelief(UUID id, Belief updates) {
        Belief belief = getBelief(id);
        if (updates.getName() != null) belief.setName(updates.getName());
        if (updates.getDescription() != null) belief.setDescription(updates.getDescription());
        if (updates.getBeliefType() != null) belief.setBeliefType(updates.getBeliefType());
        return beliefRepository.save(belief);
    }

    @Transactional
    public void deleteBelief(UUID id) {
        beliefRepository.deleteById(id);
        log.info("Belief deleted: id={}", id);
    }
}