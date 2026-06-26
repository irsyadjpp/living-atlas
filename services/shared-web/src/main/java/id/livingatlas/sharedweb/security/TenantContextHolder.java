package id.livingatlas.sharedweb.security;

/**
 * ThreadLocal holder for the current request's {@link UserContext}.
 * <p>
 * Populated by the JWT authentication filter at the start of each request
 * and cleared in a {@code finally} block to prevent memory leaks.
 * <p>
 * Usage:
 * <pre>{@code
 * UserContext user = TenantContextHolder.get().getUser();
 * if (user.hasPermission("story:write")) { ... }
 * }</pre>
 */
public class TenantContextHolder {

    private static final ThreadLocal<Context> CONTEXT = new ThreadLocal<>();

    public static void set(Context context) {
        CONTEXT.set(context);
    }

    public static Context get() {
        Context ctx = CONTEXT.get();
        if (ctx == null) {
            ctx = new Context();
            CONTEXT.set(ctx);
        }
        return ctx;
    }

    public static void clear() {
        CONTEXT.remove();
    }

    /**
     * Holds the current request's user context and tenant information.
     */
    public static class Context {
        private UserContext user;
        private String tenantId;
        private String correlationId;

        public UserContext getUser() { return user; }
        public void setUser(UserContext user) { this.user = user; }

        public String getTenantId() { return tenantId; }
        public void setTenantId(String tenantId) { this.tenantId = tenantId; }

        public String getCorrelationId() { return correlationId; }
        public void setCorrelationId(String correlationId) { this.correlationId = correlationId; }
    }
}