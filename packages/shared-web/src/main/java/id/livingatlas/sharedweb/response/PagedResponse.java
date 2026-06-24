package id.livingatlas.sharedweb.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.domain.Page;

import java.util.List;

/**
 * Standard paginated API response.
 * All list endpoints must use this format.
 *
 * @param <T> The data type
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class PagedResponse<T> {

    private List<T> data;
    private Pagination pagination;

    public PagedResponse() {}

    public PagedResponse(List<T> data, Pagination pagination) {
        this.data = data;
        this.pagination = pagination;
    }

    /**
     * Create a paged response from Spring Data Page.
     */
    public static <T> PagedResponse<T> from(Page<T> page) {
        Pagination pagination = new Pagination(
                page.getNumber() + 1,
                page.getSize(),
                page.getTotalElements(),
                page.getTotalPages(),
                page.hasNext(),
                page.hasPrevious()
        );
        return new PagedResponse<>(page.getContent(), pagination);
    }

    /**
     * Create a paged response from a list with manual pagination info.
     */
    public static <T> PagedResponse<T> of(List<T> data, int page, int pageSize, long totalItems) {
        int totalPages = (int) Math.ceil((double) totalItems / pageSize);
        Pagination pagination = new Pagination(
                page, pageSize, totalItems, totalPages,
                page < totalPages, page > 1
        );
        return new PagedResponse<>(data, pagination);
    }

    @Data
    @Builder
    @NoArgsConstructor
    public static class Pagination {
        private int page;
        private int pageSize;
        private long totalItems;
        private int totalPages;
        private boolean hasNext;
        private boolean hasPrev;

        public Pagination(int page, int pageSize, long totalItems, int totalPages, boolean hasNext, boolean hasPrev) {
            this.page = page;
            this.pageSize = pageSize;
            this.totalItems = totalItems;
            this.totalPages = totalPages;
            this.hasNext = hasNext;
            this.hasPrev = hasPrev;
        }
    }
}