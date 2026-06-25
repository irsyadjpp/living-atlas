package id.livingatlas.knowledgeservice.traditions.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.knowledgeservice.traditions.domain.Tradition;
import id.livingatlas.knowledgeservice.traditions.infrastructure.TraditionRepository;
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
public class TraditionService {

    private final TraditionRepository traditionRepository;

    @Transactional
    public Tradition createTradition(Tradition tradition) {
        tradition.setStatus("active");
        Tradition saved = traditionRepository.save(tradition);
        log.info("Tradition created: id={}, name={}", saved.getId(), saved.getName());
        return saved;
    }

    @Transactional(readOnly = true)
    public Tradition getTradition(UUID id) {
        return traditionRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Tradition not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Tradition> listTraditions(int page, int size) {
        return traditionRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Tradition updateTradition(UUID id, Tradition updates) {
        Tradition tradition = getTradition(id);
        if (updates.getName() != null) tradition.setName(updates.getName());
        if (updates.getDescription() != null) tradition.setDescription(updates.getDescription());
        if (updates.getTraditionType() != null) tradition.setTraditionType(updates.getTraditionType());
        return traditionRepository.save(tradition);
    }

    @Transactional
    public void deleteTradition(UUID id) {
        traditionRepository.deleteById(id);
        log.info("Tradition deleted: id={}", id);
    }
}