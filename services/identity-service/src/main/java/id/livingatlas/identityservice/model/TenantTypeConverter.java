package id.livingatlas.identityservice.model;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

@Converter(autoApply = true)
public class TenantTypeConverter implements AttributeConverter<TenantType, String> {

    @Override
    public String convertToDatabaseColumn(TenantType type) {
        if (type == null) {
            return null;
        }
        return type.name();
    }

    @Override
    public TenantType convertToEntityAttribute(String dbData) {
        if (dbData == null) {
            return null;
        }
        return TenantType.valueOf(dbData);
    }
}