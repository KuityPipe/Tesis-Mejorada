import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { ReservasPage } from './reservas.page';

describe('ReservasPage', () => {
  let component: ReservasPage;
  let fixture: ComponentFixture<ReservasPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ReservasPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(ReservasPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
