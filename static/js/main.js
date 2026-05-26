// Уведомления

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
        <span class="toast-icon">${type === "success" ? "✓" : "✕"}</span>
        <span class="toast-text">${message}</span>
        <button class="toast-close" onclick="dismissToast(this.parentElement)">×</button>
    `;
  container.appendChild(toast);
  setTimeout(() => dismissToast(toast), 5000);
}

function dismissToast(toast) {
  if (!toast || !toast.parentElement) return;
  toast.classList.add("toast-out");
  setTimeout(() => toast.remove(), 250);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("#toast-container .toast").forEach((t) => {
    setTimeout(() => dismissToast(t), 5000);
  });
});

// MultiSelect

class MultiSelect {
  constructor({ container, items, selected, placeholder, onChange }) {
    this.items = items;
    this.placeholder = placeholder || "Выбрать...";
    this.onChange = onChange || (() => {});

    if (selected === undefined) {
      this.selected = new Set(items.map((i) => String(i.value)));
    } else {
      this.selected = new Set(selected.map(String));
    }

    this._build(container);
  }

  _build(container) {
    container.className = "ms-wrapper";
    container.innerHTML = `
            <button type="button" class="ms-btn">
                <span class="ms-label"></span>
                <span class="ms-arrow">▾</span>
            </button>
            <div class="ms-panel" style="display:none">
                <div class="ms-search-wrap">
                    <input class="ms-search" type="text" placeholder="Поиск...">
                </div>
                <div class="ms-list"></div>
            </div>
        `;

    this.btn = container.querySelector(".ms-btn");
    this.panel = container.querySelector(".ms-panel");
    this.search = container.querySelector(".ms-search");
    this.list = container.querySelector(".ms-list");

    this._renderList("");
    this._updateLabel();

    this.btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = this.panel.style.display !== "none";
      closeAllDropdowns();
      if (!isOpen) {
        this.panel.style.display = "block";
        this.btn.classList.add("open");
        this.search.focus();
      }
    });

    this.search.addEventListener("input", () => {
      this._renderList(this.search.value.toLowerCase());
    });

    container.addEventListener("click", (e) => e.stopPropagation());
  }

  _renderList(query) {
    this.list.innerHTML = "";

    const filtered = this.items.filter((i) =>
      i.label.toLowerCase().includes(query),
    );

    // чекбокс "Выбрать все" показываем только без поиска
    if (!query) {
      const allChecked = this.selected.size === this.items.length;
      const allIndeterminate =
        this.selected.size > 0 && this.selected.size < this.items.length;

      const allLabel = document.createElement("label");
      allLabel.className = "ms-item ms-item-all";
      allLabel.innerHTML = `<input type="checkbox" ${allChecked ? "checked" : ""}><span>Выбрать все</span>`;

      const cb = allLabel.querySelector("input");
      cb.indeterminate = allIndeterminate;

      cb.addEventListener("change", (e) => {
        if (e.target.checked) {
          this.items.forEach((i) => this.selected.add(String(i.value)));
        } else {
          this.selected.clear();
        }
        this._renderList(query);
        this._updateLabel();
        this.onChange(this.getValues());
      });

      this.list.appendChild(allLabel);

      const sep = document.createElement("div");
      sep.className = "ms-separator";
      this.list.appendChild(sep);
    }

    if (filtered.length === 0) {
      const empty = document.createElement("div");
      empty.className = "ms-empty";
      empty.textContent = "Ничего не найдено";
      this.list.appendChild(empty);
      return;
    }

    filtered.forEach((item) => {
      const label = document.createElement("label");
      label.className = "ms-item";
      label.innerHTML = `
                <input type="checkbox" value="${item.value}"
                       ${this.selected.has(String(item.value)) ? "checked" : ""}>
                <span>${item.label}</span>
            `;
      label.querySelector("input").addEventListener("change", (e) => {
        const val = String(item.value);
        if (e.target.checked) this.selected.add(val);
        else this.selected.delete(val);
        this._updateSelectAll();
        this._updateLabel();
        this.onChange(this.getValues());
      });
      this.list.appendChild(label);
    });
  }

  _updateSelectAll() {
    const cb = this.list.querySelector(".ms-item-all input");
    if (!cb) return;
    cb.checked = this.selected.size === this.items.length;
    cb.indeterminate =
      this.selected.size > 0 && this.selected.size < this.items.length;
  }

  _updateLabel() {
    const label = this.btn.querySelector(".ms-label");
    const n = this.selected.size;
    const total = this.items.length;

    if (n === 0 || n === total) {
      label.textContent = this.placeholder;
    } else if (n === 1) {
      const val = Array.from(this.selected)[0];
      const item = this.items.find((i) => String(i.value) === val);
      label.textContent = item ? item.label : val;
    } else {
      label.textContent = `Выбрано: ${n}`;
    }
  }

  getValues() {
    return Array.from(this.selected);
  }

  reset(defaultSelected) {
    if (defaultSelected === undefined) {
      this.selected = new Set(this.items.map((i) => String(i.value)));
    } else {
      this.selected = new Set(defaultSelected.map(String));
    }
    this._renderList(this.search.value.toLowerCase());
    this._updateLabel();
  }
}

// SingleSelect

class SingleSelect {
  constructor({ container, items, placeholder, withSearch, onChange }) {
    this.items = items;
    this.placeholder = placeholder || "— выбрать —";
    this.withSearch = withSearch !== false;
    this.onChange = onChange || (() => {});
    this.selected = null;

    this._build(container);
  }

  _build(container) {
    container.className = "ss-wrapper";
    container.innerHTML = `
            <button type="button" class="ss-btn">
                <span class="ss-label">${this.placeholder}</span>
                <span class="ss-arrow">▾</span>
            </button>
            <div class="ss-panel" style="display:none">
                ${
                  this.withSearch
                    ? `
                <div class="ss-search-wrap">
                    <input class="ss-search" type="text" placeholder="Поиск...">
                </div>`
                    : ""
                }
                <div class="ss-list"></div>
            </div>
        `;

    this.btn = container.querySelector(".ss-btn");
    this.panel = container.querySelector(".ss-panel");
    this.search = container.querySelector(".ss-search");
    this.list = container.querySelector(".ss-list");

    this._renderList("");

    this.btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = this.panel.style.display !== "none";
      closeAllDropdowns();
      if (!isOpen) {
        this.panel.style.display = "block";
        this.btn.classList.add("open");
        if (this.search) this.search.focus();
      }
    });

    if (this.search) {
      this.search.addEventListener("input", () => {
        this._renderList(this.search.value.toLowerCase());
      });
    }

    container.addEventListener("click", (e) => e.stopPropagation());
  }

  _renderList(query) {
    this.list.innerHTML = "";
    const filtered = this.items.filter((i) =>
      i.label.toLowerCase().includes(query),
    );

    if (filtered.length === 0) {
      this.list.innerHTML = '<div class="ss-empty">Ничего не найдено</div>';
      return;
    }

    filtered.forEach((item) => {
      const div = document.createElement("div");
      div.className =
        "ss-item" +
        (String(item.value) === String(this.selected) ? " selected" : "");
      div.textContent = item.label;
      div.addEventListener("click", () => {
        this.selected = item.value;
        this._updateLabel();
        this._renderList(this.search ? this.search.value.toLowerCase() : "");
        closeAllDropdowns();
        this.onChange(item.value);
      });
      this.list.appendChild(div);
    });
  }

  _updateLabel() {
    const label = this.btn.querySelector(".ss-label");
    const item = this.items.find(
      (i) => String(i.value) === String(this.selected),
    );
    label.textContent = item ? item.label : this.placeholder;
    label.classList.toggle("ss-has-value", !!item);
  }

  getValue() {
    return this.selected;
  }
}

// Кастомные select

function initCustomSelects() {
  document.querySelectorAll("select[data-custom]").forEach((origSelect) => {
    const withSearch = origSelect.dataset.custom !== "single-no-search";

    // берем опции из исходного select
    const items = Array.from(origSelect.options)
      .filter((o) => o.value !== "")
      .map((o) => ({ value: o.value, label: o.text }));

    const placeholder = origSelect.options[0]
      ? origSelect.options[0].text
      : "выбрать";

    // вставляем обертку перед select
    const wrapper = document.createElement("div");
    origSelect.parentNode.insertBefore(wrapper, origSelect);
    origSelect.style.display = "none";

    const ss = new SingleSelect({
      container: wrapper,
      items,
      placeholder,
      withSearch,
      onChange: (val) => {
        origSelect.value = val;
      },
    });

    // если значение уже выбрано, показываем его
    if (origSelect.value) {
      ss.selected = origSelect.value;
      ss._updateLabel();
    }
  });
}

document.addEventListener("DOMContentLoaded", initCustomSelects);

// Общие функции

function closeAllDropdowns() {
  document
    .querySelectorAll(".ms-panel, .ss-panel")
    .forEach((p) => (p.style.display = "none"));
  document
    .querySelectorAll(".ms-btn.open, .ss-btn.open")
    .forEach((b) => b.classList.remove("open"));
}

document.addEventListener("click", closeAllDropdowns);

// Товары

const productsSearch = document.getElementById("products-search");

if (productsSearch) {
  productsSearch.addEventListener("input", () => {
    const q = productsSearch.value.toLowerCase().trim();
    const rows = document.querySelectorAll("tbody tr:not(.empty-row)");
    let vis = 0;

    rows.forEach((row) => {
      if (row.querySelector(".empty")) return;
      const show = !q || row.textContent.toLowerCase().includes(q);
      row.style.display = show ? "" : "none";
      if (show) vis++;
    });

    const cnt = document.getElementById("products-count");
    if (cnt) cnt.textContent = q ? `Найдено: ${vis}` : "";
  });
}

// Остатки

if (document.getElementById("ms-stock-warehouse")) {
  let warehouseMS, statusMS, productMS;

  const STATUSES = [
    { value: "in_stock", label: "На складе" },
    { value: "incoming", label: "В поставке" },
    { value: "packing", label: "На упаковке" },
  ];

  warehouseMS = new MultiSelect({
    container: document.getElementById("ms-stock-warehouse"),
    items: STOCK_WAREHOUSES.map((w) => ({
      value: String(w.id),
      label: w.name,
    })),
    placeholder: "Все склады",
    onChange: fetchStock,
  });

  statusMS = new MultiSelect({
    container: document.getElementById("ms-stock-status"),
    items: STATUSES,
    placeholder: "Все статусы",
    onChange: fetchStock,
  });

  productMS = new MultiSelect({
    container: document.getElementById("ms-stock-product"),
    items: STOCK_PRODUCTS.map((p) => ({ value: String(p.id), label: p.name })),
    placeholder: "Все товары",
    onChange: fetchStock,
  });

  document.getElementById("stock-reset-btn").addEventListener("click", () => {
    warehouseMS.reset();
    statusMS.reset();
    productMS.reset();
    fetchStock();
  });

  function fetchStock() {
    const params = new URLSearchParams();
    // если выбраны не все, передаем значения в запрос
    const wVals = warehouseMS.getValues();
    const sVals = statusMS.getValues();
    const pVals = productMS.getValues();

    if (wVals.length < STOCK_WAREHOUSES.length)
      wVals.forEach((v) => params.append("warehouse_id", v));
    if (sVals.length < STATUSES.length)
      sVals.forEach((v) => params.append("status", v));
    if (pVals.length < STOCK_PRODUCTS.length)
      pVals.forEach((v) => params.append("product_id", v));

    fetch(STOCK_API_URL + "?" + params.toString())
      .then((r) => r.json())
      .then(renderStockTable);
  }

  function renderStockTable(rows) {
    const tbody = document.getElementById("stock-tbody");

    if (rows.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="empty">Ничего не найдено</td></tr>';
    } else {
      tbody.innerHTML = rows
        .map(
          (r) => `
                <tr>
                    <td><code>${r.sku}</code></td>
                    <td>${r.product}</td>
                    <td>${r.warehouse}</td>
                    <td>
                        <select class="inline-status-select" data-stock-id="${r.id}" data-status="${r.status}">
                            <option value="incoming" ${r.status === "incoming" ? "selected" : ""}>В поставке</option>
                            <option value="in_stock" ${r.status === "in_stock" ? "selected" : ""}>На складе</option>
                            <option value="packing"  ${r.status === "packing" ? "selected" : ""}>На упаковке</option>
                        </select>
                    </td>
                    <td style="text-align:right">${r.quantity} шт.</td>
                    <td class="actions">
                        <a href="/stock/${r.id}/edit" class="btn btn-sm btn-edit">Изменить</a>
                        <form method="POST" action="/stock/${r.id}/delete"
                              onsubmit="return confirm('Удалить эту запись?')">
                            <button type="submit" class="btn btn-sm btn-delete">Удалить</button>
                        </form>
                    </td>
                </tr>
            `,
        )
        .join("");
    }

    // после перерисовки навешиваем обработчики заново
    initStockInlineStatus();

    const cnt = document.getElementById("stock-count-filter");
    const badge = document.getElementById("stock-badge");
    if (cnt) cnt.textContent = `Найдено: ${rows.length}`;
    if (badge) badge.textContent = `${rows.length} записей`;
  }
}

// Статусы остатков

function initStockInlineStatus() {
  document
    .querySelectorAll(".inline-status-select[data-stock-id]")
    .forEach((sel) => {
      // чтобы не навешивать обработчик дважды
      if (sel.dataset.statusBound) return;
      sel.dataset.statusBound = "1";

      applyInlineSelectColor(sel);

      sel.addEventListener("change", async function () {
        const stockId = this.dataset.stockId;
        const newStatus = this.value;
        const oldStatus = this.dataset.status;
        if (newStatus === oldStatus) return;

        try {
          const res = await fetch(`/api/stock/${stockId}/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus }),
          });
          const data = await res.json();

          if (!data.ok) {
            this.value = oldStatus;
            showToast("Ошибка при обновлении статуса", "error");
            return;
          }

          if (data.merged) {
            // обновляем количество в объединенной строке
            const currentRow = this.closest("tr");
            const targetSel = document.querySelector(
              `.inline-status-select[data-stock-id="${data.target_id}"]`,
            );
            if (targetSel) {
              const targetRow = targetSel.closest("tr");
              const qtyCell = targetRow.querySelector("td:nth-child(5)");
              if (qtyCell) qtyCell.textContent = data.new_quantity + " шт.";
            }
            currentRow.remove();
            showToast("Статус изменен, записи объединены", "success");
          } else {
            this.dataset.status = newStatus;
            applyInlineSelectColor(this);
            showToast("Статус обновлен", "success");
          }
        } catch {
          this.value = oldStatus;
          showToast("Ошибка соединения", "error");
        }
      });
    });
}

// статические строки
document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector(".inline-status-select[data-stock-id]")) {
    initStockInlineStatus();
  }
});

// Отгрузки

if (document.getElementById("ms-shipments-status")) {
  const SHIP_STATUSES = [
    { value: "confirmed", label: "Подтверждена" },
    { value: "in_transit", label: "В пути" },
    { value: "delivered", label: "Доставлена" },
    { value: "archived", label: "Архив" },
  ];

  // по умолчанию не показываем archived
  const DEFAULT_SELECTED = ["confirmed", "in_transit", "delivered"];

  const shipMS = new MultiSelect({
    container: document.getElementById("ms-shipments-status"),
    items: SHIP_STATUSES,
    selected: DEFAULT_SELECTED,
    placeholder: "Все статусы",
    onChange: applyShipmentsFilter,
  });

  applyShipmentsFilter(shipMS.getValues());

  function applyShipmentsFilter(selectedValues) {
    if (!selectedValues) selectedValues = shipMS.getValues();
    const rows = document.querySelectorAll("#shipments-tbody tr[data-status]");
    let vis = 0;

    rows.forEach((row) => {
      const show =
        selectedValues.length === 0 ||
        selectedValues.includes(row.dataset.status);
      row.style.display = show ? "" : "none";
      if (show) vis++;
    });

    const cnt = document.getElementById("shipments-count");
    const badge = document.getElementById("shipments-badge");
    if (cnt) cnt.textContent = `Найдено: ${vis}`;
    if (badge) badge.textContent = `${vis} записей`;
  }

  // статус меняем без перезагрузки
  document
    .querySelectorAll(".inline-status-select[data-shipment-id]")
    .forEach((sel) => {
      applyInlineSelectColor(sel);
      sel.addEventListener("change", function () {
        const id = this.dataset.shipmentId;
        const status = this.value;
        const old = this.dataset.status;

        fetch(`/api/shipments/${id}/status`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.ok) {
              this.dataset.status = status;
              this.closest("tr").dataset.status = status;
              applyInlineSelectColor(this);
              applyShipmentsFilter();
              showToast("Статус обновлен", "success");
            } else {
              this.value = old;
              showToast("Ошибка при обновлении", "error");
            }
          })
          .catch(() => {
            this.value = old;
            showToast("Ошибка соединения", "error");
          });
      });
    });
}

function applyInlineSelectColor(sel) {
  sel.dataset.status = sel.value;
}

// Форма новой отгрузки

function addItemRow() {
  const tpl = document.getElementById("item-row-template");
  const tbody = document.getElementById("items-body");
  if (tpl && tbody) tbody.appendChild(tpl.content.cloneNode(true));
}

function removeRow(btn) {
  const row = btn.closest("tr");
  const tbody = document.getElementById("items-body");
  if (tbody && tbody.querySelectorAll("tr").length > 1) row.remove();
}
