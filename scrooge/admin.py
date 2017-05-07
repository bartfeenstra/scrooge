from django.contrib.admin import ModelAdmin, register
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth import get_permission_codename
from scrooge.models import Transaction, Account, Tag


@register(Account)
class AccountAdmin(ModelAdmin):
    list_display = ('label', 'number')

    def get_form(self, request, obj=None, **kwargs):
        kwargs['fields'] = ['label']
        if obj is None:
            kwargs['fields'].insert(0, 'number')
        return super(AccountAdmin, self).get_form(request, obj, **kwargs)


@register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('description', 'amount', 'opposing_name',
                    'opposing_account_number')
    fields = ['own_account', 'opposing_account_number',
              'opposing_name', 'amount', 'description', 'tags']

    def has_change_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('change', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

    def has_delete_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('delete', opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)

    def get_changelist(self, request, **kwargs):
        return TransactionChangeList


class TransactionChangeList(ChangeList):
    def get_queryset(self, request):
        qs = super(TransactionChangeList, self).get_queryset(request)
        # Only show transactions that aren't managed by importers.
        return qs.filter(remote_id='')


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('label', 'name')

    def get_form(self, request, obj=None, **kwargs):
        kwargs['fields'] = ['label']
        if obj is None:
            kwargs['fields'].insert(0, 'name')
        return super(TagAdmin, self).get_form(request, obj, **kwargs)
