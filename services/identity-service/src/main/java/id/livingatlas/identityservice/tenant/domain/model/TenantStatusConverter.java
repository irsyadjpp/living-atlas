package id.livingatlas.identityservice.tenant.domain.model;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

@Converter(autoApply = true)
public class TenantStatusConverter implements AttributeConverter<TenantStatus, String> {

    @Override
    public String convertToDatabaseColumn(TenantStatus status) {
        if (status == null) {
            return null;
        }
        return status.name();
    }

    @Override
    public TenantStatus convertToEntityAttribute(String dbData) {
        if (dbData == null) {
            return null;
        }
        return TenantStatus.valueOf(dbData);
    }
}