from django.forms import ModelForm, TextInput, Textarea, NumberInput, RadioSelect
from Location.models import Location

class LocationForm(ModelForm) :
    class Meta :
        model = Location
        fields = [
            "name", 
            "description",
            "address",
            "province",
            "city",
            "open_hours",
            "contact_person",
            "latitude",
            "longitude",
            "category", 
        ]

        labels = {
            "name" : "Nama Lokasi",
            "description" : "Deskripsi Lokasi",
            "address" : "Alamat lokasi",
            "province" : "Provinsi lokasi",
            "city" : "Kota lokasi",
            "open_hours" : "Jam buka lokasi",
            "contact_person" : "Contact Person",
            "latitude" : "Latitude lokasi",
            "longitude" : "Longitude lokasi",
        }

        widgets = {
            "name" : TextInput(
                attrs={
                    "placeholder" : "Nama Lokasi",
                    "maxlength" : 255,
                }
            ),
            "description" : Textarea(
                attrs={
                    "placeholder" : "Ceritakan deskripsi lokasi",
                    "rows" : 3,
                }
            ),

            "address" : Textarea(
                attrs={
                    "placeholder" : "Alamat lokasi",
                    "rows" : 3,
                }
            ),
            "province" : TextInput(
                attrs={
                    "placeholder" : "Nama Provinsi",
                    "maxlength" : 255,
                }
            ),
            "city" : TextInput(
                attrs={
                    "placeholder" : "Nama Kota",
                    "maxlength" : 255,
                }
            ),
            "open_hours" : TextInput(
                attrs={
                    "placeholder" : "Jam buka lokasi",
                    "maxlength" : 255,
                }
            ),
            "contact_person" : TextInput(
                attrs={
                    "placeholder" : "Contact person yang bisa dihubungi",
                    "maxlength" : 20,
                }
            ),
            "latitude" : NumberInput(
                attrs={
                    "step": "0.000001",
                    "id": "id_latitude",
                }
            ),
            "longitude" : NumberInput(
                attrs={
                    "step": "0.000001",
                    "id": "id_longitude",
                }
            ),
            "category" : RadioSelect,
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = (
            "w-full rounded-[10px] border border-line bg-white px-3.5 py-3 "
            "text-[0.9rem] text-ink focus:border-brand focus:outline-2 focus:outline-brand"
        )
        for name, field in self.fields.items():
            if name != "category":
                field.widget.attrs["class"] = input_classes