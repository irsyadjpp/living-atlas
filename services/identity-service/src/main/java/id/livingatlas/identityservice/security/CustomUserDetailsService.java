package id.livingatlas.identityservice.security;

import id.livingatlas.identityservice.user.domain.model.User;
import id.livingatlas.identityservice.user.domain.model.UserRole;
import id.livingatlas.identityservice.user.domain.model.UserStatus;
import id.livingatlas.identityservice.rbac.domain.UserRoleRepository;
import id.livingatlas.identityservice.user.domain.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;
    private final UserRoleRepository userRoleRepository;

    @Override
    @Transactional(readOnly = true)
    public UserDetails loadUserByUsername(String emailOrUsername) throws UsernameNotFoundException {
        User user = userRepository.findByEmail(emailOrUsername)
                .orElseGet(() -> userRepository.findByUsername(emailOrUsername)
                        .orElseThrow(() -> new UsernameNotFoundException(
                                "User not found with email or username: " + emailOrUsername)));

        List<UserRole> userRoles = userRoleRepository.findAllByUserId(user.getId());

        List<SimpleGrantedAuthority> authorities = userRoles.stream()
                .map(ur -> new SimpleGrantedAuthority("ROLE_" + ur.getRole().getCode()))
                .collect(Collectors.toList());

        return new org.springframework.security.core.userdetails.User(
                user.getId().toString(),
                user.getPasswordHash(),
                user.getStatus() == UserStatus.active,
                true,
                true,
                user.getStatus() != UserStatus.blocked,
                authorities
        );
    }
}