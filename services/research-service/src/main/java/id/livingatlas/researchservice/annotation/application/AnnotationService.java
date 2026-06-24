package id.livingatlas.researchservice.annotation.application;

import id.livingatlas.researchservice.annotation.domain.Annotation;
import id.livingatlas.researchservice.annotation.infrastructure.AnnotationRepository;
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
public class AnnotationService {

    private final AnnotationRepository annotationRepository;

    @Transactional
    public Annotation createAnnotation(Annotation annotation) {
        Annotation saved = annotationRepository.save(annotation);
        log.info("Annotation created: id={}, targetType={}", saved.getId(), saved.getTargetType());
        return saved;
    }

    @Transactional(readOnly = true)
    public Annotation getAnnotation(UUID id) {
        return annotationRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Annotation not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Annotation> listAnnotations(int page, int size, String targetType, UUID targetId) {
        if (targetType != null && targetId != null) {
            return annotationRepository.findByTargetTypeAndTargetId(targetType, targetId, PageRequest.of(page, size));
        }
        return annotationRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public void deleteAnnotation(UUID id) {
        annotationRepository.deleteById(id);
        log.info("Annotation deleted: id={}", id);
    }
}