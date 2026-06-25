package id.livingatlas.identityservice.preferences.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.identityservice.preferences.domain.UserPreference;
import id.livingatlas.identityservice.preferences.infrastructure.UserPreferenceRepository;
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
public class UserPreferenceService {

    private final UserPreferenceRepository userPreferenceRepository;

    @Transactional
    public UserPreference createOrUpdatePreference(UserPreference preference) {
        UserPreference saved = userPreferenceRepository.save(preference);
        log.info("UserPreference saved: id={}, userId={}, key={}", 
                saved.getId(), saved.getUserId(), saved.getPreferenceKey());
        return saved;
    }

    @Transactional(readOnly = true)
    public UserPreference getPreference(UUID userId, String preferenceKey) {
        return userPreferenceRepository.findByUserIdAndPreferenceKey(userId, preferenceKey)
                .orElseThrow(() -> ApiException.notFound("Preference not found: " + preferenceKey));
    }

    @Transactional(readOnly = true)
    public Page<UserPreference> listPreferences(int page, int size, UUID userId) {
        if (userId != null) {
            return new org.springframework.data.domain.PageImpl<>(
                userPreferenceRepository.findByUserId(userId),
                PageRequest.of(page, size),
                userPreferenceRepository.findByUserId(userId).size()
            );
        }
        return userPreferenceRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public void deletePreference(UUID userId, String preferenceKey) {
        UserPreference preference = getPreference(userId, preferenceKey);
        userPreferenceRepository.delete(preference);
        log.info("UserPreference deleted: userId={}, key={}", userId, preferenceKey);
    }
}